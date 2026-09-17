#!/usr/bin/env python3
"""Log OBS/CLR transitions emitted by the RX Transceiver as JSON Lines."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_EVENTS = {"OBS", "CLR"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="RX serial device, e.g. COM5 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate (default: 115200)")
    parser.add_argument("--output", type=Path, help="Append JSON Lines records to this file")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial read timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import serial
    except ImportError:
        print(
            "missing dependency: install with "
            "'python -m pip install -r firmware/tools/requirements.txt'",
            file=sys.stderr,
        )
        return 2

    output = args.output.open("a", encoding="utf-8", buffering=1) if args.output else None

    try:
        with serial.Serial(args.port, args.baud, timeout=args.timeout) as connection:
            while True:
                raw = connection.readline()
                if not raw:
                    continue

                event = raw.decode("ascii", errors="replace").strip()
                if event not in VALID_EVENTS:
                    continue

                record = {
                    "event": event,
                    "received_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                }
                line = json.dumps(record, separators=(",", ":"))
                print(line, flush=True)
                if output:
                    output.write(line + "\n")
    except KeyboardInterrupt:
        return 0
    except serial.SerialException as exc:
        print(f"serial error: {exc}", file=sys.stderr)
        return 1
    finally:
        if output:
            output.close()


if __name__ == "__main__":
    raise SystemExit(main())
