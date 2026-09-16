# DL-003 — Jackal-Side Control Bridge: Serial → Persistent SSH → ROS Arbitration

**Status:** Accepted for the initial implementation  
**Date:** 2026-09-16  
**Scope:** How a STOP state received from the BLE receiver reaches and overrides normal motion control on the Clearpath Jackal

## Context

The Jackal-side NRF board receives the Radar/RIS-derived control state over BLE and exposes that state over USB serial. The question is how to move that serial event into the Jackal's ROS control path without unnecessarily installing and maintaining a second ROS environment on the laptop carried by the robot.

The Jackal itself already has an onboard computer running ROS and is reachable over Ethernet.

## Decision

For the initial implementation, the laptop mounted on the Jackal will act as a **serial-to-SSH bridge** rather than as a ROS host.

The path is:

```text
NRF RX
  |
  | USB serial
  v
Jackal-side laptop
  |
  | persistent SSH over Ethernet
  v
Jackal onboard computer
  |
  v
ROS safety-stop input
  |
  v
ROS command arbiter / mux
  |
  v
Jackal base controller
```

A small process on the laptop will:

1. keep the NRF serial port open;
2. establish an SSH session to the Jackal computer before the experiment begins;
3. keep that SSH session alive while the experiment runs; and
4. use incoming serial states to trigger the corresponding ROS-side action through that already-open session.

The laptop therefore does **not** need ROS installed for this architecture. ROS commands execute on the Jackal's onboard computer.

## Why the SSH session is persistent

Opening a new SSH connection for each STOP event would place connection establishment, authentication, and session startup in the control path for every detection.

Keeping one session open removes that repeated setup step. The serial receiver becomes the event source and the existing SSH channel becomes the transport into the Jackal computer.

The bridge can be viewed conceptually as:

```text
open serial
open SSH

while running:
    message = read serial
    if message changes the safety state:
        send corresponding command through existing SSH session
```

## ROS control semantics

The STOP requirement is a control-priority rule, not a ROS topic-priority feature.

ROS topics do not inherently have priority over one another. The implementation therefore needs a local command-arbitration mechanism on the Jackal. Normal joystick velocity commands and the Radar/RIS-derived safety state are inputs to a mux, supervisor, or equivalent control component.

```text
Joystick / normal velocity command ----\
                                        > ROS arbiter / mux --> base controller
Radar/RIS STOP ------------------------/
                higher authority
```

When STOP is asserted, the arbiter must prevent normal joystick motion from commanding the robot forward. When the safety state permits motion again, normal joystick control can resume according to the final experiment logic.

## Bring-up versus stable control logic

For early testing, the persistent SSH session can be used to invoke a ROS publish/action on the Jackal when a serial STOP event is received. This is useful for verifying the complete communication route.

The precedence rule itself remains a ROS-side responsibility. The experiment must not rely on whichever velocity message happens to arrive last; the arbitration logic must explicitly make STOP authoritative.

## Consequences

This decision has several useful consequences:

- ROS does not need to be installed on the Jackal-side laptop.
- The laptop remains a small protocol bridge: USB serial in, SSH/Ethernet out.
- The ROS control logic remains close to the robot and its existing control stack.
- BLE development, serial bridge development, and ROS arbitration can be tested separately.
- The ROS portion can be developed independently on the Jackal without requiring the sensing team to be present.

It also introduces dependencies that must be handled explicitly:

- the Ethernet link and SSH session become part of the control route;
- SSH loss must be observable rather than silently ignored;
- serial, BLE, and SSH failure behavior must be defined before the complete experiment is treated as ready; and
- the software STOP path remains an experiment-level mechanism and does not replace the Jackal's physical emergency stop or supervised safety procedures.

## Resulting design principle

The Jackal-side laptop transports the received control event into the robot computer, but **the Jackal's own ROS layer locally owns the final motion-arbitration decision**.