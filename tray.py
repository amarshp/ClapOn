"""
ClapOn system tray app.
Double-clap to open VS Code. Right-click the tray icon to pause/resume or quit.
Run: python tray.py
"""

import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse

import numpy as np
import pystray
import soundcard as sc
from PIL import Image, ImageDraw

sys.path.insert(0, "src")
from clapon.detector import ClapDetector

# ---------- Config ----------
THRESHOLD      = 0.15
SAMPLERATE     = 44100
CHUNK          = 1024
IMPULSE_MAX_MS = 150
STATE_FILE     = os.path.join(os.path.dirname(__file__), ".clapon_state")

# ---------- VS Code ----------
DB   = os.path.expandvars(r"%APPDATA%\Code\User\globalStorage\state.vscdb")
FLAG = os.path.join(os.path.expanduser("~"), ".clapon_trigger")


def _get_recent_project() -> str | None:
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


def _open_vscode() -> None:
    project = _get_recent_project()
    target = f'"{project}"' if project else ""
    with open(FLAG, "w") as f:
        f.write("1")
    subprocess.Popen(
        f"code {target}",
        shell=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


# ---------- Tray icon ----------
def _make_icon(active: bool) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (0, 200, 80, 255) if active else (140, 140, 140, 255)
    draw.ellipse([6, 6, size - 6, size - 6], fill=color)
    return img


# ---------- State persistence ----------
def _load_state() -> bool:
    try:
        return open(STATE_FILE).read().strip() == "active"
    except FileNotFoundError:
        return True  # default: active on first run


def _save_state(active: bool) -> None:
    with open(STATE_FILE, "w") as f:
        f.write("active" if active else "paused")


# ---------- Listener ----------
_active     = False
_stop_evt   = threading.Event()
_lock       = threading.Lock()


def _listen_loop() -> None:
    detector = ClapDetector(
        threshold=THRESHOLD,
        min_gap_ms=150,
        max_gap_ms=800,
        impulse_max_ms=IMPULSE_MAX_MS,
    )
    mic = sc.default_microphone()
    with mic.recorder(samplerate=SAMPLERATE, channels=1, blocksize=CHUNK) as rec:
        while not _stop_evt.is_set():
            data = rec.record(numframes=CHUNK)
            rms  = float(np.sqrt(np.mean(data ** 2)))
            if detector.feed(rms, time.monotonic()):
                _open_vscode()


def _start(tray: pystray.Icon) -> None:
    global _active, _stop_evt
    with _lock:
        if _active:
            return
        _stop_evt = threading.Event()
        threading.Thread(target=_listen_loop, daemon=True).start()
        _active = True
    tray.icon  = _make_icon(True)
    tray.title = "ClapOn — listening"
    _save_state(True)
    tray.update_menu()


def _stop(tray: pystray.Icon) -> None:
    global _active
    with _lock:
        if not _active:
            return
        _stop_evt.set()
        _active = False
    tray.icon  = _make_icon(False)
    tray.title = "ClapOn — paused"
    _save_state(False)
    tray.update_menu()


# ---------- Menu actions ----------
def _toggle(tray: pystray.Icon, item) -> None:
    if _active:
        _stop(tray)
    else:
        _start(tray)


def _quit(tray: pystray.Icon, item) -> None:
    _stop_evt.set()
    tray.stop()


def _toggle_label(item) -> str:
    return "Pause" if _active else "Resume"


# ---------- Entry point ----------
def main() -> None:
    menu = pystray.Menu(
        pystray.MenuItem(_toggle_label, _toggle, default=True),
        pystray.MenuItem("Quit", _quit),
    )
    should_start = _load_state()
    tray = pystray.Icon(
        "ClapOn",
        _make_icon(False),
        title="ClapOn — paused",
        menu=menu,
    )
    tray.run(_start if should_start else None)


if __name__ == "__main__":
    main()
