"""
Phase 3 test — double-clap opens VS Code with last project.
Run: python test_combined.py
Double-clap to trigger. Ctrl+C to stop.
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.parse

import numpy as np
import soundcard as sc

sys.path.insert(0, "src")
from clapon.detector import ClapDetector

# ---------- VS Code ----------

DB = os.path.expandvars(r"%APPDATA%\Code\User\globalStorage\state.vscdb")


def get_recent_project() -> str | None:
    con = sqlite3.connect(DB)
    row = con.execute(
        "SELECT value FROM ItemTable WHERE key='history.recentlyOpenedPathsList'"
    ).fetchone()
    con.close()
    entries = json.loads(row[0]).get("entries", [])
    for entry in entries:
        uri = entry.get("folderUri") or entry.get("fileUri")
        if uri:
            return _uri_to_path(uri)
    return None


def _uri_to_path(uri: str) -> str:
    path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return path.replace("/", "\\")


FLAG = os.path.join(os.path.expanduser("~"), ".clapon_trigger")


def open_vscode() -> None:
    project = get_recent_project()
    target = f'"{project}"' if project else ""
    print(f"  Opening: {project or 'VS Code'}", flush=True)

    # Drop the flag file — PS profile picks it up when the terminal starts
    with open(FLAG, "w") as f:
        f.write("1")

    subprocess.Popen(
        f"code {target}",
        shell=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


# ---------- Audio ----------

THRESHOLD      = 0.12
SAMPLERATE     = 44100
CHUNK          = 1024
IMPULSE_MAX_MS = 150

detector = ClapDetector(
    threshold=THRESHOLD,
    min_gap_ms=150,
    max_gap_ms=800,
    impulse_max_ms=IMPULSE_MAX_MS,
)

mic = sc.default_microphone()
print(f"Listening for double-clap (threshold={THRESHOLD})... Ctrl+C to stop.\n")

try:
    with mic.recorder(samplerate=SAMPLERATE, channels=1, blocksize=CHUNK) as rec:
        while True:
            data = rec.record(numframes=CHUNK)
            rms  = float(np.sqrt(np.mean(data ** 2)))
            now  = time.monotonic()

            if detector.feed(rms, now):
                print(">>> DOUBLE-CLAP detected!", flush=True)
                open_vscode()

except KeyboardInterrupt:
    print("\nStopped.")
