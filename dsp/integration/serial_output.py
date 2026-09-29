"""Serial transport for obstacle-state transitions (NRF Transceiver TX).

Renders semantic states as exact ``OBS``/``CLR`` lines and writes them
to the configured port. Knows nothing about radar, models, or votes:
it accepts states and transmits protocol lines.

Transition-only emission with last-transmitted tracking: a failed write
is not marked synchronized, so the next sync attempt retries it. No
message queue — two-state signaling needs none.
"""

from __future__ import annotations

from typing import Optional

from .obstacle_state import ObstacleState

BAUD = 115200

COMMANDS = {
    ObstacleState.OBSTACLE: b"OBS\n",
    ObstacleState.CLEAR: b"CLR\n",
}


class SerialStateOutput:
    """Serial writer for obstacle-state transitions.

    ``last_transmitted`` starts at CLEAR without writing anything: both
    this adapter and NRF TX boot CLEAR, so startup silence is correct
    and the first write happens only on a real transition.
    """

    def __init__(self, port: str, baud: int = BAUD, stream=None) -> None:
        self.port = port
        self.baud = baud
        self._stream = stream
        self.last_transmitted: Optional[ObstacleState] = ObstacleState.CLEAR
        self.last_error: Optional[str] = None

    def open(self) -> None:
        """Open the port. Raises with a clear message when unavailable."""
        if self._stream is not None:
            return
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required for serial output: "
                "pip install pyserial"
            ) from exc
        try:
            self._stream = serial.Serial(self.port, self.baud, timeout=1.0)
        except Exception as exc:
            raise RuntimeError(
                f"cannot open serial port {self.port!r}: {exc}"
            ) from exc

    def send(self, state: ObstacleState) -> bool:
        """Write one transition line. True on success; False records the error."""
        try:
            self._stream.write(COMMANDS[state])
            self._stream.flush()
        except Exception as exc:  # transport errors must surface, not vanish
            self.last_error = f"serial write to {self.port!r} failed: {exc}"
            return False
        self.last_error = None
        self.last_transmitted = state
        return True

    def sync(self, state: ObstacleState) -> bool:
        """Transmit only when the transport lags the semantic state.

        Covers both fresh transitions and retries after a failed write.
        """
        if self.last_transmitted == state:
            return True
        return self.send(state)

    def close(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
