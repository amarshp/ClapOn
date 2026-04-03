"""
Phase 2 test — reads last VS Code project and opens it.
Run: python test_vscode.py
"""

import json
import os
import sqlite3
import subprocess
import urllib.parse

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


project = get_recent_project()
print(f"Most recent project: {project}")

if project:
    print("Opening VS Code...")
    subprocess.Popen(
        ["code", project],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    print("Done — VS Code should be opening.")
else:
    print("No recent project found.")
