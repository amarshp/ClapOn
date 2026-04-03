# ClapOn

Double-clap near your microphone to open VS Code at your last project.

## How it works

ClapOn listens to your microphone in the background. When it detects two sharp claps within a set time window, it opens VS Code with the most recently opened project.

## Requirements

- Windows 10/11
- Python 3.11+
- VS Code installed and on your PATH (`code` command works in terminal)

## Installation

```powershell
pip install soundcard numpy
```

Clone or download this repo, then verify your mic is found:

```powershell
python check.py
```

## Usage

```powershell
python test_combined.py
```

Clap twice (about half a second apart). VS Code opens. Press `Ctrl+C` to stop.

### Optional: `jarvis` shortcut

To type `jarvis` in any terminal instead of the full command, add this to your PowerShell profile (`notepad $PROFILE`):

```powershell
function jarvis {
    python "C:\path\to\ClapOn\test_combined.py"
}
```

Replace `C:\path\to\ClapOn` with the actual path where you cloned this repo.

### Optional: open Claude in a new terminal on double-clap

Add this to the **same** PowerShell profile so new terminals started by ClapOn auto-launch Claude CLI:

```powershell
$_clapon_flag = "$env:USERPROFILE\.clapon_trigger"
if (Test-Path $_clapon_flag) {
    Remove-Item $_clapon_flag -Force
    claude
}
```

> This is optional. Without it, double-clap just opens VS Code normally.

## Tuning for your microphone

If claps are missed or background noise triggers false positives, edit the constants at the top of `test_combined.py`:

| Setting | Default | Effect |
|---|---|---|
| `THRESHOLD` | `0.08` | Minimum RMS to count as a clap. Raise if noise triggers; lower if claps are missed. |
| `IMPULSE_MAX_MS` | `150` | Max spike duration. Claps are short; sustained sounds are filtered out. |
| `min_gap_ms` | `250` | Minimum ms between the two claps. Filters out mic bounce from a single clap. |
| `max_gap_ms` | `1200` | Maximum ms between the two claps. |
| `min_silence_ms` | `200` | Refractory period after each detected clap — suppresses bounce spikes. |

Run the debug script to see what your claps look like:

```powershell
python test_clap.py
```

It prints the RMS of every spike and whether a double-clap was detected. Use `Peak RMS` to set `THRESHOLD` just below your clap level but above your noise floor.

## Files

```
src/clapon/detector.py   Core double-clap state machine (no I/O)
test_combined.py         Main script — listens and opens VS Code
test_clap.py             Debug script — shows spikes and detection in real time
test_vscode.py           Standalone test — opens VS Code without audio
check.py                 Checks that your audio device is visible to Python
```

## Compatibility note

Tested on Windows with an Intel Smart Sound Technology array microphone. Array mics produce bounce spikes — the `min_silence_ms` and `min_gap_ms` settings handle this. If you use a different mic you may need to retune `THRESHOLD` and `min_silence_ms`.
