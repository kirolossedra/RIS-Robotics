# RIS Robotics — System Design

**Status:** Draft  
**Date:** 2026-09-15  
**Scope:** End-to-end system architecture for the Radar/RIS-to-robot safety experiment

## 1. Purpose

This document is the parent system-design document for the RIS Robotics experiment. It describes the complete sensing-to-action chain at a high level before the design is decomposed into subsystem-specific files.

The primary research contribution is the Radar/RIS sensing capability. The robotics portion exists to demonstrate that a detected moving person or obstacle in the conflicting corridor can be communicated to the robot and used to prevent the robot from entering an unsafe path.

The robot is intentionally not responsible for autonomous localization, mapping, SLAM, or path planning. It is teleoperated, while a local safety mechanism on the robot has authority to override normal motion commands.

## 2. Physical Scenario

The experiment contains a corner with two corridors/routes.

- The Radar and RIS are located at the corner and are connected as part of the sensing setup.
- One corridor is covered directly by the Radar side of the sensing system.
- The other corridor is covered through the RIS side of the sensing system.
- A Jackal mobile robot travels along one route toward the corner.
- A person or other moving obstacle may be present in the conflicting route.
- If the sensing system detects a relevant moving obstacle in the conflicting corridor, the robot must not proceed into that corridor.

## 3. System-Level Behavior

The intended behavior is:

```text
No conflicting obstacle detected
        |
        v
Normal teleoperation command allowed
        |
        v
Jackal moves normally


Conflicting obstacle detected by Radar or RIS
        |
        v
Hazard state generated
        |
        v
BLE safety message broadcast by NRF board
        |
        v
Jackal-side NRF board receives message
        |
        v
Robot-side safety supervisor overrides normal motion
        |
        v
Jackal stops / is prevented from proceeding
```

The safety decision has higher priority than the operator's normal velocity command.

## 4. High-Level Architecture

```text
                    CORNER SENSING SIDE

              +-------------------------+
              |     Radar / RIS System  |
              |                         |
              | Detect moving obstacle  |
              | in conflicting corridor |
              +------------+------------+
                           |
                    hazard / clear state
                           |
                           v
                 +------------------+
                 | NRF Transmitter  |
                 | BLE broadcast    |
                 +--------+---------+
                          |
                          | BLE
                          v

                    ROBOT SIDE

                 +------------------+
                 | NRF Receiver     |
                 +--------+---------+
                          |
                          v
                 +------------------+
                 | Jackal Computer  |
                 | Safety Supervisor|
                 +--------+---------+
                          ^
                          |
              normal teleoperation / cmd_vel
                          |
                    +-----+-----+
                    | Operator  |
                    +-----------+
                          |
                          v
              Safety supervisor chooses
              whether motion is allowed
                          |
                          v
                       Jackal
```

## 5. Major System Components

### 5.1 Radar/RIS sensing system

Existing sensing subsystem responsible for detecting moving people or obstacles in the two corridor directions.

For the robotics integration, the required output is a simple safety state indicating whether the conflicting corridor should be treated as occupied/unsafe or clear.

The robot does not consume raw Radar or RIS sensing data.

### 5.2 Corner-side NRF board

Receives or is provided with the safety state from the Radar/RIS processing system and broadcasts the corresponding safety information over BLE.

The exact electrical/software interface between the sensing computer and the NRF board is still to be defined.

### 5.3 BLE communication link

BLE is the dedicated communication path for the safety state between the corner sensing setup and the robot.

This replaces the earlier Wi-Fi communication concept. Wi-Fi is not required for transferring the Radar/RIS safety decision to the robot.

The exact BLE message format, advertising behavior, update rate, timeout behavior, and failure handling are still to be defined in the communication subsystem design.

### 5.4 Jackal-side NRF board

Receives the BLE safety broadcast and provides the decoded safety state to the Jackal computer.

The physical connection and software interface between the NRF receiver and the Jackal computer are still to be defined.

### 5.5 Jackal computer

Runs the robot-side safety logic.

Its core responsibility is to combine:

- the normal teleoperation velocity command; and
- the received Radar/RIS safety state.

The safety state has higher authority than normal teleoperation.

### 5.6 Safety supervisor

The safety supervisor sits between the source of normal robot motion commands and the final command consumed by the Jackal controller.

Conceptually:

```text
Teleoperation cmd_vel -------\
                              > Safety Supervisor --> Final robot command
BLE-derived hazard state ----/
```

At the simplest level:

```text
IF conflicting corridor is unsafe:
    block forward motion / command stop
ELSE:
    allow normal teleoperation command
```

The exact ROS topic/interface design and stop semantics will be defined in the robot-control subsystem design.

### 5.7 Operator

The operator manually drives the Jackal. The operator does not make the hidden-corridor safety decision.

The Radar/RIS-derived safety mechanism can override the operator's motion command when required.

## 6. Data and Control Flows

| Flow | Source | Destination | Purpose |
|---|---|---|---|
| Moving-obstacle observation | Physical environment | Radar/RIS system | Detect motion in either corridor |
| Safety state | Radar/RIS processing | Corner NRF board | Convert sensing result into communication input |
| BLE safety broadcast | Corner NRF board | Jackal-side NRF board | Carry hazard/clear information wirelessly |
| Decoded safety state | Jackal-side NRF board | Jackal computer | Provide robot-readable safety information |
| Teleoperation command | Operator control interface | Jackal safety supervisor | Request normal robot motion |
| Final motion command | Safety supervisor | Jackal controller | Allow motion or force/prevent motion based on safety state |
| Experiment logs | Relevant software components | Data-collection laptop / storage | Record sensing, communication, and robot response timing/events |

## 7. Priority Rule

The central control rule is:

> A safety stop or motion inhibition caused by the Radar/RIS safety state must have higher priority than a normal teleoperation velocity command.

The operator must not be able to drive through an active safety stop simply by continuing to send `cmd_vel` commands.

## 8. System Boundary

### Included

- Radar/RIS safety-state output used by the robotics experiment;
- corner-side NRF integration;
- BLE safety communication;
- Jackal-side NRF integration;
- robot-side safety supervisor;
- teleoperation command arbitration;
- experiment logging needed to reconstruct sensing-to-action behavior.

### Not part of the current design objective

- autonomous navigation;
- SLAM;
- localization-based route planning;
- autonomous obstacle avoidance using the Jackal's own sensors;
- replacing the Radar/RIS detector with robot-local perception;
- benchmarking Husky versus Jackal as robotics platforms.

## 9. Hardware Platform

The current robot platform is the Clearpath Jackal.

The Jackal is intended to be used during normal working hours because moving it to the office requires additional administrative approval and a professor's signature.

The Jackal currently has a wooden rack/platform that can carry the data-collection laptop during testing.

The detailed platform tradeoff and the move from Husky to Jackal are recorded separately in the decision log.

## 10. Communication Decision

The safety communication path uses BLE with NRF boards.

The earlier design considered placing the operator, robot, and Radar/RIS computer on a common Wi-Fi network and carrying robot control, camera/video, telemetry, and safety-state traffic over that network. The design was simplified so that the safety state is instead carried through a dedicated BLE link using NRF boards.

The detailed Wi-Fi-to-BLE rationale is recorded separately in the decision log.

## 11. Logging Requirements at System Level

The experiment should eventually be able to reconstruct the sequence:

```text
Radar/RIS detection
        -> safety state generated
        -> BLE message transmitted
        -> BLE message received
        -> robot safety state updated
        -> final robot command selected
        -> robot stopped / motion allowed
```

The exact timestamp sources, log schema, and synchronization method are not yet defined.

## 12. Safety Boundary

The software safety supervisor is part of the research integration. It does not replace the Jackal's physical emergency-stop mechanism or supervised experimental procedures when people are present.

For the system design, loss-of-communication behavior, stale safety information, startup state, recovery behavior, and fail-safe semantics must be explicitly defined before human-in-the-loop testing.

## 13. Planned Decomposition

This parent document will later be decomposed into focused subsystem documents under `system/`.

Expected pieces are:

1. **Sensing Interface** — what the Radar/RIS system must expose to the robotics integration.
2. **BLE Communication** — NRF-to-NRF message protocol and failure behavior.
3. **Jackal Integration** — NRF receiver connection to the Jackal computer.
4. **Safety Supervisor** — `cmd_vel` arbitration and stop behavior.
5. **Teleoperation** — operator command path and any camera/remote-view requirements.
6. **Logging and Timing** — event logs, timestamps, and experiment reconstruction.
7. **System Safety / Failure Handling** — startup, disconnect, stale data, recovery, and emergency procedures.

These documents should refine this architecture rather than redefine the overall system independently.
