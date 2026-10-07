#!/usr/bin/env python3

import argparse
import getpass
import queue
import threading
import time

import paramiko
import serial
from serial.tools import list_ports


DEFAULT_HOST = "192.168.131.1"
DEFAULT_USER = "robot"
DEFAULT_BAUD = 115200

ROS_TOPIC = "/husky1/platform/safety_stop"
ROS_TYPE = "std_msgs/msg/Bool"

ROS_ENV = (
    "source /opt/ros/jazzy/setup.bash && "
    "export ROS_SUPER_CLIENT=True && "
    "export ROS_DOMAIN_ID=0 && "
    "export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET && "
    "export ROS_DISCOVERY_SERVER='127.0.0.1:11811;' && "
)

stateQueue = queue.Queue()
shutdownEvent = threading.Event()


def isJlink(port):
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


def discoverSerialPorts():
    ports = [port for port in list_ports.comports() if isJlink(port)]

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


class PersistentSsh:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.client = None
        self.lock = threading.Lock()

    def connect(self):
        self.close()

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(
            f"[SSH] Connecting to {self.username}@{self.hostname} ...",
            flush=True,
        )

        client.connect(
            hostname=self.hostname,
            username=self.username,
            password=self.password,
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

    def ensureConnected(self):
        if self.client is None:
            self.connect()
            return

        transport = self.client.get_transport()
        if transport is None or not transport.is_active():
            print("[SSH] Connection lost; reconnecting ...", flush=True)
            self.connect()

    def close(self):
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def runRemote(self, command, timeout=10):
        self.ensureConnected()

        remoteCommand = "bash -lc " + repr(command)

        stdin, stdout, stderr = self.client.exec_command(
            remoteCommand,
            timeout=timeout,
        )

        stdoutText = stdout.read().decode(
            "utf-8",
            errors="replace",
        ).strip()

        stderrText = stderr.read().decode(
            "utf-8",
            errors="replace",
        ).strip()

        exitCode = stdout.channel.recv_exit_status()

        return exitCode, stdoutText, stderrText

    def verifyRosPath(self):
        command = (
            ROS_ENV
            + f"ros2 topic info -v {ROS_TOPIC}"
        )

        print(
            "[SSH] Verifying ROS discovery and safety-stop topic ...",
            flush=True,
        )

        exitCode, stdoutText, stderrText = self.runRemote(
            command,
            timeout=15,
        )

        if stdoutText:
            print(f"[SSH][preflight]\n{stdoutText}", flush=True)

        if stderrText:
            print(f"[SSH][preflight stderr]\n{stderrText}", flush=True)

        if exitCode != 0:
            raise RuntimeError(
                f"ROS preflight failed with exit code {exitCode}"
            )

        if ROS_TYPE not in stdoutText:
            raise RuntimeError(
                f"{ROS_TOPIC} is not visible as {ROS_TYPE}"
            )

        if (
            "Subscription count: 0" in stdoutText
            or "Subscribers count: 0" in stdoutText
        ):
            raise RuntimeError(
                f"{ROS_TOPIC} is visible but has no subscriber"
            )

        print(
            "[SSH] ROS safety-stop path is visible",
            flush=True,
        )

    def publishSafetyState(self, isObstacle):
        rosValue = "true" if isObstacle else "false"
        label = "OBS / STOP" if isObstacle else "CLR / RELEASE"

        rosCommand = (
            ROS_ENV
            + "timeout 2 ros2 topic pub -r 10 "
            "--qos-reliability best_effort "
            f'{ROS_TOPIC} {ROS_TYPE} "{{data: {rosValue}}}"'
        )

        wrappedCommand = (
            rosCommand
            + "; code=$?; "
            + 'if [ "$code" -eq 0 ] || [ "$code" -eq 124 ]; '
            + 'then exit 0; else exit "$code"; fi'
        )

        with self.lock:
            for attempt in (1, 2):
                try:
                    print(
                        f"[SSH] {label}: publishing at 10 Hz for 2 seconds "
                        f"with BEST_EFFORT QoS",
                        flush=True,
                    )

                    exitCode, stdoutText, stderrText = self.runRemote(
                        wrappedCommand,
                        timeout=10,
                    )

                    if stdoutText:
                        print(
                            f"[SSH][stdout] {stdoutText}",
                            flush=True,
                        )

                    if stderrText:
                        print(
                            f"[SSH][stderr] {stderrText}",
                            flush=True,
                        )

                    if exitCode != 0:
                        raise RuntimeError(
                            "Remote ROS command exited with code "
                            f"{exitCode}"
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
                    self.verifyRosPath()


def serialReader(device, baud):
    try:
        connection = serial.Serial(
            device,
            baud,
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
        while not shutdownEvent.is_set():
            try:
                data = connection.read(
                    connection.in_waiting or 1
                )
            except Exception as error:
                print(
                    f"[{device}] READ ERROR: {error}",
                    flush=True,
                )
                return

            if not data:
                continue

            print(
                f"[{device}] RAW {data!r}",
                flush=True,
            )

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if line.endswith(b"\r"):
                    line = line[:-1]

                print(
                    f"[{device}] LINE {line!r}",
                    flush=True,
                )

                if line == b"OBS":
                    print(
                        f"[{device}] >>> VALID OBS <<<",
                        flush=True,
                    )
                    stateQueue.put(("OBS", device))

                elif line == b"CLR":
                    print(
                        f"[{device}] >>> VALID CLR <<<",
                        flush=True,
                    )
                    stateQueue.put(("CLR", device))

                else:
                    print(
                        f"[{device}] Ignoring non-protocol line "
                        f"{line!r}",
                        flush=True,
                    )

    finally:
        connection.close()


def bridgeWorker(ssh):
    while not shutdownEvent.is_set():
        try:
            state, device = stateQueue.get(
                timeout=0.2
            )
        except queue.Empty:
            continue

        try:
            print(
                f"[BRIDGE] {device} -> {state} -> SSH",
                flush=True,
            )

            ssh.publishSafetyState(
                state == "OBS"
            )

        except Exception as error:
            print(
                f"[BRIDGE] FAILED to apply {state}: {error}",
                flush=True,
            )

        finally:
            stateQueue.task_done()


def parseArgs():
    parser = argparse.ArgumentParser(
        description=(
            "RIS serial-to-SSH safety-stop bridge. "
            "OBS publishes safety_stop=true and CLR publishes "
            "safety_stop=false. Both use a 2-second, 10 Hz, "
            "BEST_EFFORT ROS publication with the Clearpath "
            "ROS discovery environment."
        )
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
    )

    parser.add_argument(
        "--user",
        default=DEFAULT_USER,
    )

    parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD,
    )

    return parser.parse_args()


def main():
    args = parseArgs()

    print(
        "RIS serial -> SSH -> ROS safety-stop bridge v2\n"
        f"Robot: {args.user}@{args.host}\n"
        f"Topic: {ROS_TOPIC}\n"
        "OBS => true, 10 Hz for 2 s, BEST_EFFORT\n"
        "CLR => false, 10 Hz for 2 s, BEST_EFFORT\n"
        "Clearpath ROS discovery environment: explicit\n",
        flush=True,
    )

    password = getpass.getpass(
        f"SSH password for {args.user}@{args.host}: "
    )

    ssh = PersistentSsh(
        hostname=args.host,
        username=args.user,
        password=password,
    )

    try:
        ssh.connect()

        # Do not accept serial safety commands unless the exact
        # non-interactive SSH environment can see the live ROS path.
        ssh.verifyRosPath()

        ports = discoverSerialPorts()

        worker = threading.Thread(
            target=bridgeWorker,
            args=(ssh,),
            daemon=True,
        )
        worker.start()

        for port in ports:
            thread = threading.Thread(
                target=serialReader,
                args=(
                    port.device,
                    args.baud,
                ),
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
        print(
            "\nStopping bridge ...",
            flush=True,
        )

    finally:
        shutdownEvent.set()
        ssh.close()


if __name__ == "__main__":
    main()
