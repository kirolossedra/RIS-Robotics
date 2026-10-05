#!/usr/bin/env python3

import threading
import time

import serial
from serial.tools import list_ports

BAUD = 115200


def is_jlink(port):
    text = " ".join(
        str(value or "")
        for value in (
            port.description,
            port.manufacturer,
            port.product,
            port.hwid,
        )
    ).lower()

    return (
        port.vid == 0x1366
        or "segger" in text
        or "j-link" in text
        or "jlink" in text
    )


def monitor(device):
    try:
        connection = serial.Serial(
            device,
            BAUD,
            timeout=0.1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
    except Exception as error:
        print(f"[{device}] OPEN FAILED: {error}", flush=True)
        return

    print(f"[{device}] OPEN", flush=True)

    buffer = b""

    while True:
        try:
            data = connection.read(connection.in_waiting or 1)
        except Exception as error:
            print(f"[{device}] ERROR: {error}", flush=True)
            return

        if not data:
            continue

        print(f"[{device}] RAW {data!r}", flush=True)
        buffer += data

        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)

            if line.endswith(b"\r"):
                line = line[:-1]

            print(f"[{device}] LINE {line!r}", flush=True)

            if line == b"OBS":
                print(f"[{device}] >>> VALID OBS <<<", flush=True)
            elif line == b"CLR":
                print(f"[{device}] >>> VALID CLR <<<", flush=True)


ports = [port for port in list_ports.comports() if is_jlink(port)]

print("Detected J-Link serial interfaces:", flush=True)

for port in ports:
    print(
        f"  {port.device} | "
        f"{port.description} | "
        f"VID={port.vid} PID={port.pid}",
        flush=True,
    )

if not ports:
    raise SystemExit("NO SEGGER/J-Link serial interfaces detected")

for port in ports:
    threading.Thread(
        target=monitor,
        args=(port.device,),
        daemon=True,
    ).start()

print("\nListening for stub-mode serial output. Press Ctrl+C to stop.\n", flush=True)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
