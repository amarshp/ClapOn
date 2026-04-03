"""
Phase 1 test — double-clap detection using soundcard (WASAPI).
Run: python test_clap.py
Clap twice near your mic. Ctrl+C to stop early.
"""

import sys
import time
import numpy as np
import soundcard as sc

sys.path.insert(0, "src")
from clapon.detector import ClapDetector

THRESHOLD       = 0.10
SAMPLERATE      = 44100
CHUNK           = 1024
DURATION        = 10
IMPULSE_MAX_MS  = 300   # claps are short sharp spikes; sustained sounds filtered out

detector = ClapDetector(
    threshold=THRESHOLD,
    min_gap_ms=80,
    max_gap_ms=1200,
    impulse_max_ms=IMPULSE_MAX_MS,
)

clap_count = 0
peak_rms   = 0.0

# -- debug spike tracking --
in_spike       = False
spike_start    = 0.0
chunk_duration = CHUNK / SAMPLERATE   # ~23ms

mic = sc.default_microphone()
print(f"Mic      : {mic.name}")
print(f"Threshold: {THRESHOLD}   impulse_max: {IMPULSE_MAX_MS}ms")
print(f"Listening for {DURATION}s — double-clap near your mic...\n")

start = time.monotonic()

try:
    with mic.recorder(samplerate=SAMPLERATE, channels=1, blocksize=CHUNK) as rec:
        while time.monotonic() - start < DURATION:
            data = rec.record(numframes=CHUNK)
            rms  = float(np.sqrt(np.mean(data ** 2)))
            now  = time.monotonic()

            if rms > peak_rms:
                peak_rms = rms

            # Debug: print spike start/end and duration
            if rms >= THRESHOLD and not in_spike:
                in_spike    = True
                spike_start = now
                print(f"  [spike start] rms={rms:.4f}", flush=True)
            elif rms < THRESHOLD and in_spike:
                in_spike = False
                dur_ms = (now - spike_start) * 1000
                print(f"  [spike end  ] duration={dur_ms:.0f}ms", flush=True)

            if detector.feed(rms, now):
                clap_count += 1
                print(f"\n  >>> DOUBLE-CLAP #{clap_count} <<<\n", flush=True)

except KeyboardInterrupt:
    pass

elapsed = time.monotonic() - start
print(f"\n--- Results after {elapsed:.1f}s ---")
print(f"Peak RMS : {peak_rms:.4f}  (threshold={THRESHOLD})")
print(f"Claps    : {clap_count}")
