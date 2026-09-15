# DL-001 — Radar/RIS-to-Robot Communication: Wi-Fi to BLE

**Status:** Accepted  
**Date:** 2026-09-15  
**Scope:** Communication path carrying the Radar/RIS obstacle state to the mobile robot

## Context

The experiment requires the Radar/RIS sensing system to notify the mobile robot when a moving person or obstacle is detected in the conflicting corridor. The robot is teleoperated; the sensing system is not responsible for navigation. Its role is to provide a compact safety state that can be consumed by a robot-side supervisor with higher priority than normal velocity commands.

The information crossing this interface is intentionally small. The robot does not need raw radar or RIS data. It only needs the derived state required for the experiment, such as `HAZARD` / `CLEAR` or an equivalent compact message.

## Initial decision — Wi-Fi

The first architecture considered a shared Wi-Fi LAN containing the operator computer, robot computer, and Radar/RIS processing computer.

Under that design, Wi-Fi would carry several traffic classes:

- operator velocity commands to the robot;
- camera/video data from the robot to the remote operator;
- Radar/RIS safety state to the robot;
- robot telemetry and experiment logs;
- supporting ROS/network-discovery traffic where applicable.

This was attractive because it reused the robot's normal IP networking and would make the Radar/RIS safety state easy to expose as a network or ROS message.

## Revised decision — BLE using Nordic NRF boards

The communication architecture was simplified. The Radar/RIS safety signal will now use Bluetooth Low Energy rather than Wi-Fi.

An NRF board on the Radar/RIS side will broadcast the derived obstacle/safety state using BLE. A second NRF board associated with the robot computer will receive that BLE message and expose the state to the robot-side software.

Conceptually:

```text
Radar / RIS detection
        |
        v
Derived safety state
        |
        v
NRF board -- BLE broadcast --> NRF board -- local interface --> Robot computer
                                                        |
                                                        v
                                                Safety supervisor
```

The robot-side supervisor will then decide whether normal motion commands are allowed to reach the robot controller.

## Why the decision changed

BLE is a better fit for this specific interface because the information being transferred is only a small control/safety state rather than a high-bandwidth data stream.

Moving this signal to BLE:

- reduces the communication implementation to a small, explicit interface;
- avoids coupling the Radar/RIS safety trigger to the Wi-Fi network used for teleoperation or camera streaming;
- avoids unnecessary IP/ROS networking complexity for a binary or otherwise compact state;
- makes the Radar/RIS-to-robot path independently testable;
- reuses NRF hardware already suitable for BLE development;
- keeps the robotics integration subordinate to the actual sensing contribution rather than turning networking into a second research problem.

## Consequences

The camera stream and remote teleoperation may still use the robot's normal networking as needed, but they are no longer part of the Radar/RIS safety communication path.

The BLE receiver must provide a clean local interface to the robot computer so the safety supervisor can consume the received state and override motion when necessary.

The implementation must also define what happens when BLE messages are stale or missing. Silence must not automatically be treated as proof that the corridor is clear. This is especially important because the experiment involves a moving robot and people. BLE is the experiment's communication mechanism, not a substitute for the robot's physical emergency-stop provisions or normal human safety procedures.

## Resulting design principle

The sensing computer decides **whether the conflicting corridor is occupied**. BLE communicates that result. The robot computer retains the local authority to enforce the stop.
