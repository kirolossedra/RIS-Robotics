#!/usr/bin/env python3
"""Two-board TX -> BLE -> RX smoke test for the RIS Transceiver.

Opens the TX and RX VCOM consoles (Zephyr console, 115200 8N1), then
checks the episode contract from firmware/README.md:

    wireless: OBS OBS OBS OBS CLR CLR CLR OBS OBS
    serial:   OBS             CLR         OBS

Repeated broadcasts must produce exactly one host event each.
Leaves the link idling CLR.

Usage:
    python smoke_test.py --tx COM14 --rx COM8

Role discovery: if the roles are unknown, run once; a silent run means
the ports are swapped (RX ignores serial input), so swap --tx/--rx.

Requires: pyserial (firmware/tools/requirements.txt).
"""
from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
except ImportError:
    print("missing dependency: install with "
          "'python -m pip install -r firmware/tools/requirements.txt'",
          file=sys.stderr)
    raise SystemExit(2)


def drain(connection: serial.Serial, duration: float = 1.0) -> list[str]:
    deadline = time.time() + duration
    lines: list[str] = []
    while time.time() < deadline:
        raw = connection.readline()
        if raw:
            lines.append(raw.decode("ascii", errors="replace").strip())
    return lines


def send(connection: serial.Serial, command: str, repeat: int = 3) -> None:
    for _ in range(repeat):
        connection.write((command + "\n").encode())
        time.sleep(0.15)


def check_episode(tx: serial.Serial, rx: serial.Serial) -> bool:
    for connection in (tx, rx):
        connection.reset_input_buffer()
    send(tx, "OBS")
    obs1 = drain(rx, 3.0)
    print(f"OBS x3 -> {obs1}", flush=True)
    for connection in (tx, rx):
        connection.reset_input_buffer()
    send(tx, "CLR")
    clr = drain(rx, 3.0)
    print(f"CLR x3 -> {clr}", flush=True)
    for connection in (tx, rx):
        connection.reset_input_buffer()
    send(tx, "OBS")
    obs2 = drain(rx, 3.0)
    print(f"OBS x3 again -> {obs2}", flush=True)
    ok = obs1 == ["OBS"] and clr == ["CLR"] and obs2 == ["OBS"]
    send(tx, "CLR")
    drain(rx, 2.0)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tx", required=True,
                        help="TX console serial port, e.g. COM14")
    parser.add_argument("--rx", required=True,
                        help="RX console serial port, e.g. COM8")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    tx = serial.Serial(args.tx, args.baud, timeout=0.5)
    rx = serial.Serial(args.rx, args.baud, timeout=0.5)
    try:
        ok = check_episode(tx, rx)
    finally:
        tx.close()
        rx.close()
    print("SMOKE:", "PASS" if ok else "FAIL", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
