#!/usr/bin/env python3

import os
import queue
import shutil
import subprocess
import threading
import time

import serial
from serial.tools import list_ports


# Deployment binding: changes if the CONTROLLED_ROBOT network address changes.
# A different robot does not require a bridge-logic change if it is reachable at
# the same address and exposes the same ROS safety-stop interface.
SSH_HOST = "192.168.131.1"

# Deployment/account binding: changes if the remote operating-system account
# changes. It is independent of the serial protocol and OBS/CLR semantics.
SSH_USER = "robot"

# Credential is intentionally not hardcoded. The environment variable name is
# stable unless the credential-delivery convention changes.
SSH_PASSWORD = os.environ["RIS_ROBOT_SSH_PASSWORD"]

# Serial transport contract: expected to survive robot/network changes while the
# nRF Transceiver host interface remains 115200 8N1. Change only if that serial
# contract changes.
BAUD = 115200

# Deployment/ROS namespace binding: changes if the CONTROLLED_ROBOT namespace or
# safety-stop topic changes. A robot swap can preserve this value if it exposes
# the same topic path.
ROS_TOPIC = "/husky1/platform/safety_stop"

# ROS interface contract: expected to survive IP, host, and namespace changes.
# Change only if the safety-stop message contract itself stops using Bool.
ROS_TYPE = "std_msgs/msg/Bool"

# Remote process-management conventions: expected to survive normal robot and
# network changes as long as the remote host provides writable /tmp storage.
# Change if process supervision, permissions, or filesystem policy changes.
REMOTE_PID_FILE = "/tmp/ris-safety-publisher.pid"
REMOTE_LOG_FILE = "/tmp/ris-safety-publisher.log"

# Remote ROS environment binding. The Jazzy setup path depends on the installed
# ROS distribution/location. The discovery variables depend on the robot's ROS
# network topology. They can survive a robot replacement only when that new
# deployment intentionally uses the same ROS environment and discovery layout.
ROS_ENV = (
    "source /opt/ros/jazzy/setup.bash && "
    "export ROS_SUPER_CLIENT=True ROS_DOMAIN_ID=0 "
    "ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
    "ROS_DISCOVERY_SERVER='127.0.0.1:11811;' && "
)

state_queue = queue.Queue()
shutdown_event = threading.Event()


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


def discover_serial_ports():
    ports = [port for port in list_ports.comports() if is_jlink(port)]

    print("Detected SEGGER/J-Link serial interfaces:", flush=True)

    for port in ports:
        print(
            f"  {port.device} | {port.description} | "
            f"VID={port.vid} PID={port.pid}",
            flush=True,
        )

    if not ports:
        raise RuntimeError("No SEGGER/J-Link serial interfaces detected")

    return ports


def build_remote_command(state):
    if state == "OBS":
        ros_value = "true"
    elif state == "CLR":
        ros_value = "false"
    else:
        raise ValueError(f"Unsupported state: {state}")

    # Behavioral control policy, not merely deployment configuration:
    # - 2 seconds bounds each remote publisher lifetime;
    # - 10 Hz repeats the state during that window;
    # - BEST_EFFORT is the QoS used by the physically exercised path.
    # These values should survive ordinary host/IP/robot-binding changes. Change
    # them only when the stop/release timing or ROS reliability design changes,
    # and revalidate the resulting control behavior.
    publish_command = (
        "timeout 2 ros2 topic pub -r 10 "
        "--qos-reliability best_effort "
        f'{ROS_TOPIC} {ROS_TYPE} "{{data: {ros_value}}}"'
    )

    return (
        ROS_ENV
        + f"PIDFILE={REMOTE_PID_FILE}; "
        + 'if [ -s "$PIDFILE" ]; then '
        + 'OLDPID=$(cat "$PIDFILE" 2>/dev/null || true); '
        + 'if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then '
        + 'kill -- -"$OLDPID" 2>/dev/null || kill "$OLDPID" 2>/dev/null || true; '
        + 'fi; '
        + 'fi; '
        + 'rm -f "$PIDFILE"; '
        + f"nohup setsid {publish_command} "
        + f"> {REMOTE_LOG_FILE} 2>&1 < /dev/null & "
        + 'NEWPID=$!; '
        + 'echo "$NEWPID" > "$PIDFILE"; '
        + f'echo "STARTED {state} PID=$NEWPID"'
    )


def run_ssh_state(state):
    remote_command = build_remote_command(state)

    command = [
        "sshpass",
        "-p",
        SSH_PASSWORD,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
        f"{SSH_USER}@{SSH_HOST}",
        remote_command,
    ]

    label = "OBS / STOP" if state == "OBS" else "CLR / RELEASE"

    print(
        f"[SSH] {label}: preempt previous publisher and start newest state",
        flush=True,
    )

    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )

    if result.stdout.strip():
        print(
            f"[SSH][stdout] {result.stdout.strip()}",
            flush=True,
        )

    if result.stderr.strip():
        print(
            f"[SSH][stderr] {result.stderr.strip()}",
            flush=True,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"SSH scheduling command failed with exit code {result.returncode}"
        )

    print(
        f"[SSH] {label}: newest state is now publishing "
        "at 10 Hz for 2 seconds, BEST_EFFORT",
        flush=True,
    )


def serial_reader(device):
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
        print(
            f"[{device}] OPEN FAILED: {error}",
            flush=True,
        )
        return

    print(f"[{device}] OPEN", flush=True)
    buffer = b""

    try:
        while not shutdown_event.is_set():
            try:
                data = connection.read(connection.in_waiting or 1)
            except Exception as error:
                print(
                    f"[{device}] READ ERROR: {error}",
                    flush=True,
                )
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
                    print(
                        f"[{device}] >>> VALID OBS <<<",
                        flush=True,
                    )
                    state_queue.put(("OBS", device))

                elif line == b"CLR":
                    print(
                        f"[{device}] >>> VALID CLR <<<",
                        flush=True,
                    )
                    state_queue.put(("CLR", device))

                else:
                    print(
                        f"[{device}] Ignoring non-protocol line {line!r}",
                        flush=True,
                    )

    finally:
        connection.close()


def bridge_worker():
    while not shutdown_event.is_set():
        try:
            state, device = state_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        consumed = 1
        while True:
            try:
                newer_state, newer_device = state_queue.get_nowait()
                state = newer_state
                device = newer_device
                consumed += 1
            except queue.Empty:
                break

        try:
            print(
                f"[BRIDGE] {device} -> {state} -> preemptive SSH scheduler",
                flush=True,
            )
            run_ssh_state(state)

        except Exception as error:
            print(
                f"[BRIDGE] FAILED to apply {state}: {error}",
                flush=True,
            )

        finally:
            for _ in range(consumed):
                state_queue.task_done()


def main():
    print(
        "RIS serial -> preemptive SSH -> ROS safety-stop bridge\n"
        f"Robot: {SSH_USER}@{SSH_HOST}\n"
        f"Topic: {ROS_TOPIC}\n"
        "OBS => true, 10 Hz for 2 s, BEST_EFFORT\n"
        "CLR => false, 10 Hz for 2 s, BEST_EFFORT\n"
        "Scheduling: newest state preempts previous publisher\n"
        "SSH password: supplied through RIS_ROBOT_SSH_PASSWORD\n",
        flush=True,
    )

    if shutil.which("sshpass") is None:
        raise RuntimeError(
            "sshpass is not installed. Install it with: sudo apt install sshpass"
        )

    ports = discover_serial_ports()

    worker = threading.Thread(
        target=bridge_worker,
        daemon=True,
    )
    worker.start()

    for port in ports:
        thread = threading.Thread(
            target=serial_reader,
            args=(port.device,),
            daemon=True,
        )
        thread.start()

    print(
        "\nBridge active. Waiting for exact OBS/CLR lines. "
        "Press Ctrl+C to stop.\n",
        flush=True,
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bridge ...", flush=True)
    finally:
        shutdown_event.set()


if __name__ == "__main__":
    main()
