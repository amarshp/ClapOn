"""
Double-clap state machine. Pure logic, no I/O.

A "clap" = a short spike (< impulse_max_ms) followed by silence.
A "double-clap" = two claps with a gap of min_gap_ms to max_gap_ms.
"""

import time
from enum import Enum, auto


class _State(Enum):
    IDLE = auto()
    FIRST = auto()       # got one clap, waiting for second
    COOLDOWN = auto()    # triggered, ignoring input


class ClapDetector:
    def __init__(
        self,
        threshold: float = 0.25,
        min_gap_ms: int = 150,
        max_gap_ms: int = 800,
        impulse_max_ms: int = 60,
        cooldown_s: float = 3.0,
    ) -> None:
        self.threshold = threshold
        self.min_gap_ms = min_gap_ms
        self.max_gap_ms = max_gap_ms
        self.impulse_max_s = impulse_max_ms / 1000.0
        self.cooldown_s = cooldown_s

        self._state = _State.IDLE
        self._spike_start: float | None = None
        self._first_clap_at: float = 0.0
        self._triggered_at: float = 0.0

    def feed(self, rms: float, now: float | None = None) -> bool:
        """Feed one chunk's RMS. Returns True when a double-clap is confirmed."""
        t = now if now is not None else time.monotonic()
        is_spike = rms >= self.threshold
        clap_ended = self._track_impulse(is_spike, t)

        if self._state is _State.COOLDOWN:
            if t - self._triggered_at >= self.cooldown_s:
                self._state = _State.IDLE
            return False

        if self._state is _State.IDLE:
            if clap_ended:
                self._state = _State.FIRST
                self._first_clap_at = t
            return False

        # FIRST state — waiting for the second clap
        elapsed_ms = (t - self._first_clap_at) * 1000

        if elapsed_ms > self.max_gap_ms:
            # Window expired — treat as fresh first clap if one just ended
            if clap_ended:
                self._first_clap_at = t
            else:
                self._state = _State.IDLE
            return False

        if clap_ended and elapsed_ms >= self.min_gap_ms:
            self._state = _State.COOLDOWN
            self._triggered_at = t
            return True

        return False

    def _track_impulse(self, is_spike: bool, t: float) -> bool:
        """Returns True once when a short spike ends (= a clap impulse)."""
        if is_spike:
            if self._spike_start is None:
                self._spike_start = t
            return False
        if self._spike_start is not None:
            duration = t - self._spike_start
            self._spike_start = None
            return duration <= self.impulse_max_s
        return False
