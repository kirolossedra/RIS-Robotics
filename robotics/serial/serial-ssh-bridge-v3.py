#!/usr/bin/env python3

import os
import queue
import threading
import time

import paramiko
import serial
from serial.tools import list_ports


SSH_HOST = "192.168.131.1"
SSH_USER = "robot"
SSH_PASSWORD = os.environ["RIS_ROBOT_SSH_PASSWORD"]

BAUD = 115200

ROS_SETUP = "/home/robot/clearpath/setup.bash"
ROS_TOPIC = "/husky1/platform/safety_stop"
ROS_TYPE = "std_msgs/msg/Bool"

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


class PersistentSSH:
    def __init__(self):
        self.client = None
        self.lock = threading.Lock()

    def connect(self):
        self.close()

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(
            f"[SSH] Connecting to {SSH_USER}@{SSH_HOST} ...",
            flush=True,
        )

        client.connect(
            hostname=SSH_HOST,
            username=SSH_USER,
            password=SSH_PASSWORD,
            look_for_keys=False,
            allow_agent=False,
            timeout=10,
            banner_timeout=10,
            auth_timeout=10,
        )

        transport = client.get_transport()
        if transport is not None:
            transport.set_keepalive(15)

        self.client = client
        print("[SSH] Connected", flush=True)

    def close(self):
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def ensure_connected(self):
        if self.client is None:
            self.connect()
            return

        transport = self.client.get_transport()
        if transport is None or not transport.is_active():
            print("[SSH] Connection lost; reconnecting ...", flush=True)
            self.connect()

    def run_command(self, command, timeout=10):
        self.ensure_connected()

        stdin, stdout, stderr = self.client.exec_command(
            command,
            timeout=timeout,
        )

        exit_code = stdout.channel.recv_exit_status()

        stdout_text = stdout.read().decode(
            "utf-8",
            errors="replace",
        ).strip()

        stderr_text = stderr.read().decode(
            "utf-8",
            errors="replace",
        ).strip()

        return exit_code, stdout_text, stderr_text

    def publish_safety_state(self, obstacle):
        ros_value = "true" if obstacle else "false"
        label = "OBS / STOP" if obstacle else "CLR / RELEASE"

        remote_command = (
            f"source {ROS_SETUP} && "
            "export ROS_SUPER_CLIENT=True && "
            "timeout 2 ros2 topic pub -r 10 "
            "--qos-reliability best_effort "
            f'{ROS_TOPIC} {ROS_TYPE} "{{data: {ros_value}}}"'
        )

        with self.lock:
            for attempt in (1, 2):
                try:
                    print(
                        f"[SSH] {label}: executing specific remote ROS command",
                        flush=True,
                    )
                    print(
                        f"[SSH] {label}: 10 Hz for 2 seconds, BEST_EFFORT",
                        flush=True,
                    )

                    exit_code, stdout_text, stderr_text = self.run_command(
                        remote_command,
                        timeout=10,
                    )

                    if stdout_text:
                        print(
                            f"[SSH][stdout]\n{stdout_text}",
                            flush=True,
                        )

                    if stderr_text:
                        print(
                            f"[SSH][stderr]\n{stderr_text}",
                            flush=True,
                        )

                    if exit_code not in (0, 124):
                        raise RuntimeError(
                            f"Remote command exited with code {exit_code}"
                        )

                    print(
                        f"[SSH] {label}: publication complete",
                        flush=True,
                    )
                    return

                except Exception as error:
                    print(
                        f"[SSH] {label}: attempt {attempt} failed: {error}",
                        flush=True,
                    )

                    self.close()

                    if attempt == 2:
                        raise

                    self.connect()


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


def bridge_worker(ssh):
    while not shutdown_event.is_set():
        try:
            state, device = state_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        try:
            print(
                f"[BRIDGE] {device} -> {state} -> SSH command",
                flush=True,
            )

            ssh.publish_safety_state(state == "OBS")

        except Exception as error:
            print(
                f"[BRIDGE] FAILED to apply {state}: {error}",
                flush=True,
            )

        finally:
            state_queue.task_done()


def main():
    print(
        "RIS serial -> specific SSH command -> ROS safety-stop bridge v3\n"
        f"Robot: {SSH_USER}@{SSH_HOST}\n"
        f"ROS setup: {ROS_SETUP}\n"
        f"Topic: {ROS_TOPIC}\n"
        "OBS => true, 10 Hz for 2 s, BEST_EFFORT\n"
        "CLR => false, 10 Hz for 2 s, BEST_EFFORT\n"
        "SSH password: built into script\n",
        flush=True,
    )

    ssh = PersistentSSH()

    try:
        ssh.connect()

        exit_code, stdout_text, stderr_text = ssh.run_command(
            f"test -f {ROS_SETUP} && echo CLEARPATH_SETUP_OK",
            timeout=5,
        )

        if exit_code != 0 or "CLEARPATH_SETUP_OK" not in stdout_text:
            raise RuntimeError(
                f"Clearpath ROS setup file not found at {ROS_SETUP}"
            )

        print("[SSH] Clearpath ROS setup file found", flush=True)

        ports = discover_serial_ports()

        worker = threading.Thread(
            target=bridge_worker,
            args=(ssh,),
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

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping bridge ...", flush=True)

    finally:
        shutdown_event.set()
        ssh.close()


if __name__ == "__main__":
    main()
