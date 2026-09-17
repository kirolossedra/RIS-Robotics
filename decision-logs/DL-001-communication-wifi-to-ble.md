# DL-001 — Radar/RIS-to-Robot Communication: Wi-Fi to BLE

**Status:** Accepted  
**Date:** 2026-09-15; implementation detail updated 2026-09-16  
**Scope:** Communication path carrying the Radar/RIS obstacle state to the mobile robot

## Context

The experiment requires the Radar/RIS sensing system to notify the mobile robot when a moving person or obstacle is detected in the conflicting corridor. The robot is teleoperated; the sensing system is not responsible for navigation. Its role is to provide a compact safety state that can be consumed by a robot-side supervisor with higher control authority than normal velocity commands.

The information crossing this interface is intentionally small. The robot does not need raw radar or RIS data. It only needs the derived state required for the experiment, represented on the Transceiver boundary as `OBS` / `CLR`.

The current integration assumption is that the Infineon radar is connected by USB to the sensing computer, that this computer drives the radar, and that the relevant Radar/RIS detection information is processed in a real-time pipeline on that computer. The exact point at which the object-detection event is exposed still needs confirmation from the sensing team.

## Initial decision — Wi-Fi

The first architecture considered a shared Wi-Fi LAN containing the operator computer, robot computer, and Radar/RIS processing computer.

Under that design, Wi-Fi could have carried several traffic classes:

- operator velocity commands to the robot;
- camera/video data from the robot to the remote operator;
- Radar/RIS safety state to the robot;
- robot telemetry and experiment logs; and
- supporting ROS/network-discovery traffic where applicable.

This was technically workable, but it coupled the small safety signal to a broader network and made the robotics integration larger than necessary.

## Revised decision — BLE using Nordic NRF boards

The Radar/RIS safety signal will use Bluetooth Low Energy rather than Wi-Fi.

An NRF board on the Radar/RIS side runs the TX role of the shared Transceiver firmware, receives `OBS` / `CLR` over USB serial, and broadcasts the latched state using BLE Coded PHY S=8. A second board runs the RX role, receives repeated BLE messages, and exposes only state transitions over USB serial to the laptop mounted on the robot.

Conceptually:

```text
Radar / RIS processing pipeline
            |
            v
    Object-detection event
            |
            v
       USB serial
            |
            v
         NRF TX
            |
           BLE
            |
            v
         NRF RX
            |
            v
       USB serial
            |
            v
   Jackal-side laptop
```

Two NRF boards are already available, so no additional BLE hardware is currently expected. The TX-to-RX BLE portion is targeted to be operational before the 2026-09-17 team session.

## Why the decision changed

BLE is a better fit for this specific interface because the information being transferred is only a small control/safety state rather than a high-bandwidth stream.

Moving this signal to BLE:

- makes the sensing-to-robot interface explicit and independently testable;
- decouples the safety trigger from Wi-Fi used for unrelated teleoperation or camera traffic;
- avoids requiring raw Radar/RIS data to cross to the robot;
- avoids unnecessary IP/ROS networking complexity on the sensing-to-robot wireless hop;
- reuses the available NRF hardware; and
- keeps the robotics integration subordinate to the actual sensing contribution rather than turning networking into a second research problem.

## Sensing-team boundary

The only external integration required for the BLE path is a clean detection event from the existing sensing pipeline.

The sensing team needs to confirm:

1. where the required object-detection event is available in the current pipeline; and
2. whether a small serial-output step can be inserted there so the event can be delivered to the NRF transmitter.

The sensing team does not need to implement the BLE receiver or Jackal-side ROS control path.

## Robot-side consequence

BLE terminates at the NRF receiver; it does not directly control the Jackal.

The receiver feeds the Jackal-side laptop over USB serial. Under the current robot-side architecture, that laptop can maintain a persistent SSH session over Ethernet to the Jackal onboard computer. A received STOP event can therefore cause a ROS-side action to execute on the Jackal without requiring ROS to be installed on the laptop itself.

The priority rule is not implemented by making a ROS topic intrinsically "higher priority." A ROS-side arbiter/mux/supervisor must enforce STOP authority over normal joystick velocity commands.

The detailed robot-side decision is recorded separately in **DL-003**.

## Reliability consequence

The implementation must define what happens when BLE messages are stale or missing. The same applies to serial or SSH failure downstream. Silence or loss of connectivity must not automatically be treated as proof that the corridor is clear.

This software path is part of the research experiment and does not replace the robot's physical emergency-stop provisions or normal supervised procedures.

## Resulting design principle

The sensing computer decides **whether the relevant conflicting condition has been detected**. BLE carries only that compact result. The Jackal's ROS control layer retains local authority to enforce the resulting stop.
