# Serial-to-SSH Bridge Explanation and Operation

## Contents

- [Purpose](#purpose)
- [Current status](#current-status)
- [Versioning model](#versioning-model)
- [End-to-end control path](#end-to-end-control-path)
- [Serial protocol behavior](#serial-protocol-behavior)
- [Why the serial output is transition-oriented](#why-the-serial-output-is-transition-oriented)
- [How the implementation evolved](#how-the-implementation-evolved)
  - [Serial validation — `serial-test.py`](#serial-validation--serial-testpy)
  - [Bridge v1 — initial Paramiko bridge](#bridge-v1--initial-paramiko-bridge)
  - [Bridge v2 — explicit ROS discovery preflight](#bridge-v2--explicit-ros-discovery-preflight)
  - [Bridge v3 — Clearpath setup-path experiment](#bridge-v3--clearpath-setup-path-experiment)
  - [Bridge v4 — exact SSH remote commands](#bridge-v4--exact-ssh-remote-commands)
  - [Bridge v5 — source ROS Jazzy](#bridge-v5--source-ros-jazzy)
  - [Bridge v6 — intermediate discovery checkpoint](#bridge-v6--intermediate-discovery-checkpoint)
  - [Bridge v7 — reproduce the live Clearpath ROS environment](#bridge-v7--reproduce-the-live-clearpath-ros-environment)
  - [Bridge v8 — preemptive latest-state-wins scheduling](#bridge-v8--preemptive-latest-state-wins-scheduling)
- [Current canonical design](#current-canonical-design)
- [Hardcoded deployment and behavior assumptions](#hardcoded-deployment-and-behavior-assumptions)
- [ROS command semantics](#ros-command-semantics)
- [How to operate the current bridge](#how-to-operate-the-current-bridge)
  - [Prerequisites](#prerequisites)
  - [One-time host setup](#one-time-host-setup)
  - [Run the bridge](#run-the-bridge)
  - [Put the Transceiver in RX mode](#put-the-transceiver-in-rx-mode)
  - [Stub-mode validation](#stub-mode-validation)
  - [Normal BLE operation](#normal-ble-operation)
- [Expected runtime behavior](#expected-runtime-behavior)
- [Troubleshooting notes learned during integration](#troubleshooting-notes-learned-during-integration)
- [Known limitations and next concern](#known-limitations-and-next-concern)
- [Version history](#version-history)

## Purpose

This document explains how the RIS Robotics serial-to-SSH bridge reached its current working implementation, why each historical stage changed, and how to operate the current canonical bridge.

The bridge owns the integration boundary between the RX Transceiver's newline-delimited `OBS` / `CLR` serial output and the existing `CONTROLLED_ROBOT` ROS safety-stop interface.

It does **not** replace Clearpath's local motion arbitration. The existing `twist_mux` remains the authority that blocks or restores lower-priority velocity sources.

## Current status

As of 2026-10-05, the following path has been physically exercised successfully:

```text
RX Transceiver serial
        |
        | OBS / CLR
        v
serial-ssh-bridge.py
        |
        | specific SSH remote command
        v
CONTROLLED_ROBOT onboard computer
        |
        | ROS 2 Bool publication
        v
/husky1/platform/safety_stop
        |
        v
Clearpath twist_mux
        |
        +-- OBS / true  -> motion blocked
        |
        +-- CLR / false -> motion restored
```

The current working implementation is:

```text
robotics/serial/serial-ssh-bridge.py
```

The serial transport itself was validated before SSH integration using:

```text
robotics/serial/serial-test.py
```

## Versioning model

There is one bridge source file: `robotics/serial/serial-ssh-bridge.py`.

Historical bridge stages are represented by commits to that same path. Numbered source filenames are not used as version identity. The version labels below are descriptive names for the engineering sequence; the commit hash is the precise source identity.

This matters because the former v6 checkpoint documented an intended discovery change that was not actually present in the executable artifact. Under the commit-based model, an implementation claim must point to the commit that contains it. The v6 checkpoint is therefore intentionally represented by an empty commit, making the absence of an executable change explicit rather than hiding it behind a filename.

The canonical consolidation that removed the numbered files and documented the runtime assumptions is commit `09e102368726b5de8aeff4b959547f223e3b5f63`.

## End-to-end control path

The current integration path is:

```mermaid
flowchart LR
    RX["nRF52833 RX Transceiver"]
    SERIAL["USB CDC serial\nOBS / CLR"]
    HOST["Controlled Robot-side host\nserial-ssh-bridge.py"]
    SSH["Specific SSH remote command"]
    ROS["/husky1/platform/safety_stop\nstd_msgs/msg/Bool"]
    MUX["Clearpath twist_mux"]
    BASE["CONTROLLED_ROBOT"]

    RX --> SERIAL --> HOST --> SSH --> ROS --> MUX --> BASE
```

The bridge therefore translates only the safety state:

| Serial state | ROS value | Meaning |
|---|---:|---|
| `OBS` | `true` | Assert software safety stop |
| `CLR` | `false` | Release software safety stop |

The physical emergency stop remains independent and higher priority than this software path.

## Serial protocol behavior

The validated RX serial protocol is deliberately small:

```text
OBS\n
CLR\n
```

Host parsing is newline-delimited. Raw operating-system reads are **not** treated as message boundaries.

For example, the following is valid serial behavior:

```text
RAW b'O'
RAW b'BS\n'
LINE b'OBS'
```

Likewise:

```text
RAW b'C'
RAW b'LR\n'
LINE b'CLR'
```

The important evidence is the completed parsed line, not whether one `read()` call happened to return the whole message.

The bridge ignores any completed line other than exact `OBS` or exact `CLR`.

## Why the serial output is transition-oriented

The RX firmware deduplicates repeated logical states. Repeated BLE or synthetic `OBS` events do not continuously flood the serial host, and repeated `CLR` events are likewise suppressed.

Conceptually:

```text
CLEAR -> OBS   => emit OBS once
OBS   -> OBS   => emit nothing
OBS   -> CLEAR => emit CLR once
CLEAR -> CLEAR => emit nothing
```

This behavior exists because BLE state advertising can repeat the same state many times. The serial boundary was designed as a transition stream rather than a continuous state stream.

This behavior was accepted for the current implementation and is not considered a serial failure.

A consequence remains: if the host bridge starts or reconnects after a transition has already happened and the RX state does not change again, the deduplication layer does not automatically replay the current state. State resynchronization is therefore a separate future design concern.

## How the implementation evolved

### Serial validation — `serial-test.py`

Before SSH was introduced, the serial boundary was isolated and tested by itself.

The listener:

- auto-detected SEGGER/J-Link CDC interfaces;
- opened the available ACM ports;
- printed raw byte chunks;
- reconstructed newline-delimited messages;
- accepted only exact `OBS` and `CLR` lines.

Physical stub-mode testing proved complete `OBS` and `CLR` framing on `/dev/ttyACM0`.

This established an important boundary: subsequent failures were no longer assumed to be serial failures unless the parsed `LINE` output itself was incorrect.

### Bridge v1 — initial Paramiko bridge

Canonical-history commit: `8ca39312dbc00d147b93c055245e7b1ccb7cbffb`.

The first complete bridge added SSH and invoked the already-proven ROS safety-stop publication remotely.

Both state changes used the same publication policy:

```text
10 Hz for 2 seconds
BEST_EFFORT QoS
```

rather than a one-shot publication.

This matched the earlier physical ROS experiment in which repeated BEST_EFFORT publication was the reliable operating procedure, especially for release.

v1 successfully:

- read `OBS` / `CLR` from serial;
- authenticated over SSH;
- launched `ros2 topic pub` remotely.

However, the robot did not react. The remote process existed, but it was not participating in the same ROS discovery environment as the working interactive shell.

### Bridge v2 — explicit ROS discovery preflight

Canonical-history commit: `f7f19d84c4d71fbb601ebb0ed17850a748d2dfe2`.

v2 attempted to make the ROS environment explicit and added a preflight check for:

```text
/husky1/platform/safety_stop
```

The preflight failed with:

```text
Unknown topic '/husky1/platform/safety_stop'
```

This proved that successfully launching the ROS CLI was not enough; the non-interactive SSH command needed the robot's actual ROS discovery context.

### Bridge v3 — Clearpath setup-path experiment

Canonical-history commit: `33149f3ca4d11e9cfa63da06e3d6667d4d1d9d7a`.

v3 attempted to reproduce the robot environment by sourcing a guessed Clearpath setup file.

That path did not exist on this robot, so the version failed before bridge operation.

The important lesson was to stop guessing robot-specific setup paths and instead reproduce only values directly observed in the working shell.

### Bridge v4 — exact SSH remote commands

Canonical-history commit: `8d98c715faf84c4ba603250337c1e2b8651363e1`.

v4 simplified the transport model.

Instead of treating SSH as an interactive session, the bridge used the same conceptual operation as:

```text
ssh robot@192.168.131.1 '<specific command>'
```

This matched the intended architecture: each serial transition causes a specific remote ROS command.

The next failure was explicit:

```text
timeout: failed to run command 'ros2': No such file or directory
```

The SSH command reached the robot correctly; the non-interactive shell simply did not have ROS 2 on its `PATH`.

### Bridge v5 — source ROS Jazzy

Canonical-history commit: `47b496ca0367a69dba9e982b548cf742d220079f`.

v5 prefixed both remote commands with:

```bash
source /opt/ros/jazzy/setup.bash
```

This made the `ros2` executable available remotely.

The command could now launch, but publication still did not affect the live ROS graph because the Clearpath discovery variables were still absent.

### Bridge v6 — intermediate discovery checkpoint

Canonical-history commit: `81fb03b251245ee715d87a3b6d09fa9652afee85`.

This is intentionally an empty executable-change commit. The historical v6 attempt was supposed to introduce the discovery fix, but the generated/executed source remained byte-for-byte equivalent to the v5 source.

Operationally it therefore behaved like v5. The empty commit records the checkpoint honestly: there was an engineering attempt and a claimed stage, but no corresponding code change in the bridge artifact.

This is the failure mode that motivated commit-based artifact identity instead of numbered filenames.

### Bridge v7 — reproduce the live Clearpath ROS environment

Canonical-history commit: `7b2278a72dd219e62c6414e5d4186a97cef4a083`.

The working interactive SSH shell was inspected directly and exposed:

```text
ROS_SUPER_CLIENT=True
ROS_DOMAIN_ID=0
ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ROS_DISCOVERY_SERVER=127.0.0.1:11811;
```

A direct remote command that sourced Jazzy and exported those exact values was tested while observing `/husky1/platform/safety_stop`. Both `true` and `false` were seen on the ROS topic.

v7 therefore reproduced the actual environment instead of inferring it.

At this point the serial command, SSH execution, ROS environment, and Bool semantics were all individually correct.

The remaining issue was scheduling.

v7 executed each two-second publication synchronously. Therefore a new state could wait behind an older state that was still publishing.

For example:

```text
OBS received
    |
    v
publish true for 2 seconds
    |
    | CLR arrives here but waits
    v
OBS command finishes
    |
    v
publish false for 2 seconds
```

This was especially undesirable for a safety path because a newer state should become authoritative immediately rather than waiting in FIFO order behind a stale command.

### Bridge v8 — preemptive latest-state-wins scheduling

Canonical-history commit: `a27e8c8db522f9f0645706f346035641e408ffda`.

v8 changed the scheduler from sequential command completion to **latest-state-wins** behavior.

Each new state:

1. checks whether a previous RIS ROS publisher is still running;
2. kills the previous publisher process group;
3. starts the new publisher in its own remote session/process group;
4. records the new remote PID;
5. returns immediately from SSH while the bounded two-second ROS publisher runs remotely.

The remote PID is tracked in:

```text
/tmp/ris-safety-publisher.pid
```

and publisher output is written to:

```text
/tmp/ris-safety-publisher.log
```

The local queue also collapses accumulated transitions so stale queued states are discarded and the newest state is applied.

Conceptually:

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> PublishingOBS: OBS
    Idle --> PublishingCLR: CLR
    PublishingOBS --> PublishingCLR: CLR preempts OBS
    PublishingCLR --> PublishingOBS: OBS preempts CLR
    PublishingOBS --> PublishingOBS: newer OBS remains authoritative
    PublishingCLR --> PublishingCLR: newer CLR remains authoritative
```

This behavior was physically exercised successfully for both STOP and release.

## Current canonical design

The current bridge has four important responsibilities.

### 1. Serial discovery and framing

It finds SEGGER/J-Link CDC interfaces and reads at:

```text
115200 baud
8 data bits
no parity
1 stop bit
```

It reconstructs messages using newline framing and accepts only exact `OBS` or `CLR`.

### 2. State translation

```text
OBS -> Bool(true)
CLR -> Bool(false)
```

### 3. ROS environment reproduction

Each remote command explicitly sources ROS 2 Jazzy and exports the Clearpath ROS discovery environment observed on the robot.

### 4. Preemptive scheduling

The newest serial state supersedes any still-running older publisher.

This prevents a stale two-second publication from blocking the next state transition.

## Hardcoded deployment and behavior assumptions

The bridge intentionally keeps the currently validated values in the source. They are **documented assumptions**, not all treated as values that must be externalized. Each value has a different stability boundary.

| Value | Classification | What can require a change | What normally does not require a change |
|---|---|---|---|
| `SSH_HOST = "192.168.131.1"` | Deployment/network binding | CONTROLLED_ROBOT IP addressing or network topology changes | Serial protocol changes; replacing hardware while preserving the same reachable address |
| `SSH_USER = "robot"` | Remote-account binding | OS image/account policy or login user changes | Robot IP changes; ROS topic changes |
| `RIS_ROBOT_SSH_PASSWORD` environment variable | Credential-delivery convention | Secret-delivery mechanism or environment-variable naming policy changes | Password value changes, because the secret itself is not committed |
| `BAUD = 115200` with 8N1 | Serial transport contract | nRF host serial configuration changes | CONTROLLED_ROBOT IP, ROS namespace, SSH account, or robot hardware changes that leave the nRF serial contract intact |
| `ROS_TOPIC = "/husky1/platform/safety_stop"` | Deployment/ROS namespace binding | Robot namespace or selected safety-stop topic changes | IP changes; SSH account changes; same interface exposed under the same namespace |
| `ROS_TYPE = "std_msgs/msg/Bool"` | ROS interface contract | Safety-stop API/message semantics change | IP, username, topic namespace changes that preserve the Bool contract |
| `/tmp/ris-safety-publisher.pid` | Remote process-management convention | Process supervision strategy, permissions, or filesystem policy changes | Normal network changes or robot replacement with compatible `/tmp` semantics |
| `/tmp/ris-safety-publisher.log` | Remote logging convention | Logging/supervision strategy, permissions, or filesystem policy changes | Normal network changes or robot replacement with compatible `/tmp` semantics |
| `/opt/ros/jazzy/setup.bash` | ROS installation binding | ROS distribution or installation location changes | IP/SSH changes; same Jazzy installation on a replacement host |
| `ROS_SUPER_CLIENT=True` | ROS discovery-environment binding | Clearpath/ROS discovery architecture changes | Serial framing changes; network address changes that retain the same discovery model |
| `ROS_DOMAIN_ID=0` | ROS domain binding | Deployment moves to another ROS domain | Robot hardware replacement within the same ROS domain |
| `ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET` | ROS discovery-topology binding | Discovery scope/topology changes | Host replacement that keeps the same subnet discovery design |
| `ROS_DISCOVERY_SERVER='127.0.0.1:11811;'` | ROS discovery-server binding | Discovery server address/port or deployment architecture changes | Remote IP changes when the discovery server remains local to that remote host |
| publisher lifetime `2 s` | Behavioral/control policy | Stop/release timing design changes after measurement and validation | IP, username, namespace, or robot-binding changes by themselves |
| publication rate `10 Hz` | Behavioral/control policy | Reliability/latency design changes after validation | Ordinary deployment addressing changes |
| `BEST_EFFORT` QoS | Behavioral/interface policy | ROS reliability contract or measured delivery requirements change | Ordinary deployment addressing changes |

The last three values are especially important: `2 s`, `10 Hz`, and `BEST_EFFORT` are not merely machine-specific defaults. They are part of the currently exercised control behavior. They should not be changed simply to make the code look configurable; changing them changes the behavior that has been physically exercised and therefore requires renewed validation.

The source file contains the same classification next to the hardcoded values so that an engineer editing the bridge does not have to infer which constants are deployment bindings and which are behavioral contracts.

## ROS command semantics

Both states use the same bounded repeated-publication mechanism.

The effective STOP command is:

```bash
timeout 2 ros2 topic pub -r 10 --qos-reliability best_effort \
  /husky1/platform/safety_stop std_msgs/msg/Bool "{data: true}"
```

The effective release command is:

```bash
timeout 2 ros2 topic pub -r 10 --qos-reliability best_effort \
  /husky1/platform/safety_stop std_msgs/msg/Bool "{data: false}"
```

The bridge intentionally does **not** use a one-shot publication for either state.

The two-second repeated BEST_EFFORT form is retained because it is the procedure that restored motion reliably during the earlier ROS-side physical experiment.

## How to operate the current bridge

### Prerequisites

The current implementation assumes:

- Linux host connected to the RX Transceiver over USB;
- Ethernet connectivity to the `CONTROLLED_ROBOT` onboard computer;
- `CONTROLLED_ROBOT` binding is the current Clearpath Husky A200 at `192.168.131.1`;
- SSH user is `robot`;
- ROS 2 Jazzy and the existing Clearpath stack are running on the robot;
- `/husky1/platform/safety_stop` remains the active software safety-lock topic;
- `pyserial` is installed on the host;
- `sshpass` is installed on the host;
- the physical emergency stop remains accessible during physical motion testing.

### One-time host setup

Install the Python serial dependency if needed:

```bash
python3 -m pip install pyserial
```

Install `sshpass` if needed:

```bash
sudo apt install sshpass
```

The committed repository version reads the SSH credential from:

```text
RIS_ROBOT_SSH_PASSWORD
```

Set that environment variable in the host shell before running the bridge.

### Run the bridge

From the repository root:

```bash
export RIS_ROBOT_SSH_PASSWORD='<robot-password>'
python3 robotics/serial/serial-ssh-bridge.py
```

Expected startup includes discovery of the J-Link CDC interfaces followed by:

```text
Bridge active. Waiting for exact OBS/CLR lines.
```

The integration session physically observed the valid protocol on `/dev/ttyACM0`. The bridge opens all matching J-Link interfaces and processes whichever one produces valid protocol lines.

### Put the Transceiver in RX mode

The unified Transceiver firmware boots in TX mode.

From the default boot state, press **Button 2 once** to enter RX mode.

Expected RX Natural LED state under the current firmware mapping:

```text
LED1: steady ON
LED2: normally OFF except receive pulse
LED3: ON for Coded S=8
LED4: OFF in Natural stub mode
```

### Stub-mode validation

Button 3 cycles the RX stub source:

```text
Natural
  |
  | Button 3
  v
Forced CLR
  |
  | Button 3
  v
Forced OBS
  |
  | Button 3
  v
Natural
```

Important: moving from **Forced OBS to Natural emits no synthetic serial state**. Therefore after observing `OBS`, one Button 3 press may correctly produce no new serial line. Pressing Button 3 again moves Natural to Forced CLR and produces `CLR`.

Expected bridge evidence for OBS:

```text
LINE b'OBS'
>>> VALID OBS <<<
[BRIDGE] ... -> OBS -> preemptive SSH scheduler
[SSH] OBS / STOP: ...
```

Expected bridge evidence for CLR:

```text
LINE b'CLR'
>>> VALID CLR <<<
[BRIDGE] ... -> CLR -> preemptive SSH scheduler
[SSH] CLR / RELEASE: ...
```

### Normal BLE operation

Stub mode is only a local RX validation mechanism.

In normal operation the RX Transceiver remains in Natural mode and receives `OBS` / `CLR` state through BLE from the TX Transceiver. The host bridge does not need to know whether a validated RX state originated from BLE or the development stub; it only consumes the resulting serial protocol line.

## Expected runtime behavior

### OBS path

```text
RX emits OBS\n
    |
    v
bridge parses OBS
    |
    v
newest state becomes OBS
    |
    v
previous remote RIS publisher is terminated if still active
    |
    v
remote true publisher starts
    |
    v
/husky1/platform/safety_stop = true
    |
    v
twist_mux blocks lower-priority motion
```

### CLR path

```text
RX emits CLR\n
    |
    v
bridge parses CLR
    |
    v
newest state becomes CLR
    |
    v
previous remote RIS publisher is terminated if still active
    |
    v
remote false publisher starts
    |
    v
/husky1/platform/safety_stop = false
    |
    v
twist_mux permits normal lower-priority control again
```

## Troubleshooting notes learned during integration

### Split raw reads are normal

Do not diagnose this as corruption:

```text
RAW b'O'
RAW b'BS\n'
```

The parser correctly reconstructs `OBS` once the newline arrives.

### No output after one stub-button press can be correct

From Forced OBS, Button 3 moves to Natural first. Natural does not inject a synthetic state. Another Button 3 press is required to reach Forced CLR.

### `ros2: No such file or directory`

A non-interactive SSH command does not automatically inherit the ROS CLI path. The working bridge explicitly sources:

```text
/opt/ros/jazzy/setup.bash
```

### ROS command runs but robot does not react

The Clearpath ROS discovery environment must also be reproduced. The working values observed on this robot are:

```text
ROS_SUPER_CLIENT=True
ROS_DOMAIN_ID=0
ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ROS_DISCOVERY_SERVER=127.0.0.1:11811;
```

### CLR waits behind OBS in older versions

That was the v7 scheduling problem. The current canonical bridge does not intentionally wait for the previous two-second publication to finish; the newest state preempts it.

## Known limitations and next concern

The bridge is now functionally able to carry both `OBS` and `CLR` through serial, SSH, ROS, and the existing Clearpath safety-stop interface.

However, **functional correctness is not the same as acceptable stop latency**.

The current path still includes several potentially significant timing components:

```text
serial detection
    + host scheduling
    + new SSH command execution
    + remote shell startup
    + ROS CLI process startup
    + ROS discovery / publisher creation
    + twist_mux lock handling
    + controller response
    + physical robot deceleration
```

The current implementation therefore must not be described as latency-validated.

The observed physical system has already motivated concern about how quickly the robot actually reaches zero motion after `OBS`. That concern should be evaluated separately from this document's conclusion that the **state path itself now works**.

The next design discussion should focus on reducing and measuring trigger-to-stop latency without discarding the evidence and working behavior established here.

## Version history

| Stage | Canonical commit | Main change | Outcome |
|---|---|---|---|
| Serial validation utility | `09e102368726b5de8aeff4b959547f223e3b5f63` | Canonicalized the isolated RX serial listener as `serial-test.py` | Existing serial `OBS` / `CLR` validation preserved without a numbered filename |
| Bridge v1 | `8ca39312dbc00d147b93c055245e7b1ccb7cbffb` | Initial serial + Paramiko SSH + ROS command | SSH command ran, robot did not react |
| Bridge v2 | `f7f19d84c4d71fbb601ebb0ed17850a748d2dfe2` | Explicit ROS discovery/preflight attempt | Safety topic not visible |
| Bridge v3 | `33149f3ca4d11e9cfa63da06e3d6667d4d1d9d7a` | Tried robot-specific setup path | Assumed path did not exist |
| Bridge v4 | `8d98c715faf84c4ba603250337c1e2b8651363e1` | Switched to direct specific SSH command execution | `ros2` missing from non-interactive PATH |
| Bridge v5 | `47b496ca0367a69dba9e982b548cf742d220079f` | Source ROS 2 Jazzy | ROS CLI available; discovery still incomplete |
| Bridge v6 | `81fb03b251245ee715d87a3b6d09fa9652afee85` | Historical checkpoint; no executable diff from v5 | Makes the missing intended change explicit |
| Bridge v7 | `7b2278a72dd219e62c6414e5d4186a97cef4a083` | Added exact observed Clearpath ROS discovery variables | ROS state reached graph; synchronous scheduling remained |
| Bridge v8 | `a27e8c8db522f9f0645706f346035641e408ffda` | Added preemptive latest-state-wins remote scheduling | **Working OBS and CLR bridge** |
| Canonical consolidation | `09e102368726b5de8aeff4b959547f223e3b5f63` | Removed numbered bridge files, renamed the serial test, and documented hardcoded-value stability boundaries in source | One active bridge file with Git-based version identity |
