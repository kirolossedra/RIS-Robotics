# Decision: Controlled Robot Control Bridge (Serial → Local ROS)

**ID:** `robot-ros-0001`  
**Previous ID:** `DL-003`  
**Status:** Accepted — current architecture  
**Original date:** 2026-09-17  
**Updated:** 2026-10-05  
**Scope:** How a STOP state received from the BLE receiver reaches and overrides normal motion control on the Controlled Robot

**Current hardware binding:** `CONTROLLED_ROBOT` = Clearpath Husky A200, updated 2026-10-04. This platform choice is a binding, not the architectural identity used by this control decision. The earlier Jackal selection remains in the dated hardware-selection history.

## Contents

- [Context](#context)
- [Decision](#decision)
- [Why the SSH session is persistent](#why-the-ssh-session-is-persistent)
- [ROS control semantics](#ros-control-semantics)
- [Bring-up versus stable control logic](#bring-up-versus-stable-control-logic)
- [Consequences](#consequences)
- [Resulting design principle](#resulting-design-principle)
- [Archived Decisions](#archived-decisions)

## Context

The Controlled Robot-side NRF board receives the Radar/RIS-derived control state over BLE and exposes that state over USB serial. The 2026-10-05 serial integration smoke test proved the complete route by connecting the NRF RX to an external laptop, forwarding the received serial state through SSH, and publishing the corresponding ROS safety-stop state on the Controlled Robot onboard computer. Both STOP and release were physically validated.

That SSH route was therefore a **smoke-test transport**, not the intended stable architecture.

## Decision

The NRF RX USB serial connection will be plugged **directly into the Controlled Robot onboard computer**.

A persistent local bridge process on the Controlled Robot computer will:

1. keep the NRF RX serial interface open;
2. parse exact `OBS` / `CLR` messages;
3. keep a local ROS publisher alive in the Controlled Robot ROS environment; and
4. publish the corresponding state directly into the local ROS safety-stop interface.

The active path becomes:

```text
NRF RX
  |
  | USB serial
  v
Controlled Robot onboard computer
  |
  | persistent local serial / ROS bridge
  v
ROS safety-stop input
  |
  v
ROS command arbiter / mux
  |
  v
Controlled Robot base controller
```

The external laptop, Ethernet hop, SSH transport, remote shell, and remote ROS CLI invocation are removed from the active stopping path.

The transport-independent semantics remain unchanged:

```text
OBS -> assert software safety STOP
CLR -> explicitly release software safety STOP
```

Silence, malformed input, stale input, or serial disconnect must not automatically mean `CLR`.

## Why the SSH session is persistent

SSH is no longer part of the current runtime decision. This section is retained only because the original decision used SSH and the historical rationale remains relevant to the archived smoke-test architecture below.

The smoke-test path attempted to keep SSH work out of the event path where possible because connection establishment, authentication, remote shell startup, and ROS CLI startup add dependencies and latency. The direct-USB architecture removes those concerns entirely from the normal stop path rather than optimizing them further.

## Next validation

The next test is the **direct USB path**:

1. plug the NRF RX USB directly into the Controlled Robot onboard computer;
2. identify the serial device carrying `OBS` / `CLR`;
3. run a local bridge inside the robot's ROS environment;
4. confirm `OBS` is parsed and reaches the local safety-stop interface;
5. physically validate STOP;
6. confirm `CLR` is parsed and reaches the local safety-stop interface;
7. physically validate release; and
8. measure end-to-end stopping latency separately from functional correctness.

The already validated SSH bridge remains useful as smoke-test evidence and a diagnostic reference, but it is no longer the target runtime path.

## ROS control semantics

The Controlled Robot has only two logical motion-control authorities:

1. normal teleoperation / `cmd_vel`;
2. higher-priority safety STOP.

Distance-to-corner is contextual state used to gate whether STOP is enforced. It is **not** a third control authority.

The Radar-side range calculation and proposed 2.0 m `TRIGGER` remain separate from this transport decision. The Controlled Robot's local arbiter still enforces STOP precedence.

The current Clearpath binding uses the existing local safety-stop path. The software safety stop remains below the physical emergency stop, so this architecture does not replace or weaken the physical emergency stop.

## Bring-up versus stable control logic

The serial → SSH → ROS route is now explicitly classified as **bring-up / smoke-test infrastructure**.

The stable target is serial → local ROS on the Controlled Robot computer. The test path proved the semantics and interfaces before collapsing the architecture onto the robot itself.

## Consequences

The active architecture now:

- removes the external laptop from the critical stopping path;
- removes Ethernet and SSH from the critical stopping path;
- keeps serial reception and ROS publication on the same onboard computer;
- allows ROS discovery and publisher state to remain established in one persistent local process;
- reduces the number of runtime dependencies between `OBS` reception and local stop arbitration; and
- is expected to reduce software-side stopping latency, although the improvement must be measured rather than assumed.

The direct-host path must still validate serial-device discovery, reconnect behavior, ROS environment startup, malformed/stale input handling, STOP/release behavior, and measured stopping latency.

## Resulting design principle

**The Controlled Robot owns its received safety input locally.**

The NRF RX feeds the Controlled Robot computer directly, and a persistent local bridge translates serial state into the robot's local ROS safety-stop interface. SSH remains a bring-up and diagnostic mechanism, not part of the intended stopping path.

## Archived Decisions

### 2026-09-17 — Serial → SSH → ROS initial implementation

**Status:** Superseded on 2026-10-05 after successful smoke testing.  
**Reason for supersession:** The SSH route successfully proved the complete serial-to-ROS control path. The next architecture removes the test-only external laptop and SSH transport and validates direct USB into the Controlled Robot onboard computer.

For the initial implementation, the laptop mounted on the Controlled Robot was to act as a **serial-to-SSH bridge** rather than as a ROS host.

The path was:

```text
NRF RX
  |
  | USB serial
  v
Controlled Robot-side laptop
  |
  | persistent SSH over Ethernet
  v
Controlled Robot onboard computer
  |
  v
ROS safety-stop input
  |
  v
ROS command arbiter / mux
  |
  v
Controlled Robot base controller
```

A small process on the laptop would:

1. keep the NRF serial port open;
2. establish an SSH session to the Controlled Robot computer before the experiment began;
3. keep that SSH session alive while the experiment ran; and
4. use incoming serial states to trigger the corresponding ROS-side action through that already-open session.

The laptop therefore did **not** need ROS installed. ROS commands executed on the Controlled Robot's onboard computer.

Opening a new SSH connection for each STOP event was recognized as undesirable because it would place connection establishment, authentication, and session startup in the event path. The original concept therefore preferred a persistent SSH channel:

```text
open serial
open SSH

while running:
    message = read serial
    if message changes the safety state:
        send corresponding command through existing SSH session
```

During 2026-10-05 bring-up, the actual smoke-test implementation evolved through multiple serial-to-SSH bridge versions until both STOP and release worked end to end. That validated the communication route while confirming that SSH was serving as a test harness rather than a necessary architectural boundary.

The original decision's core principle remains valid: **the Controlled Robot's own ROS layer locally owns the final motion-arbitration decision**.
