"""Quick diagnostic — exits on its own after each step."""
import sys

print("Step 1: importing sounddevice...", flush=True)
try:
    import sounddevice as sd
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    sys.exit(1)

print("Step 2: listing audio devices...", flush=True)
try:
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i}] {d['name']}  (inputs={d['max_input_channels']})", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    sys.exit(1)

print("Step 3: default input device...", flush=True)
try:
    default = sd.query_devices(kind='input')
    print(f"  {default['name']}", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)

print("Done.", flush=True)
