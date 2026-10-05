# Robotics Controller and Integration

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Child directories](#child-directories)
- [Documentation boundaries](#documentation-boundaries)
- [Current material](#current-material)

## Purpose

This directory owns robot-side controller setup and integration documentation, including how protocol behavior is bound to the ROS control stack. Runtime implementations belong in their actual source packages.

## Scope

Use this area for controller and robot-integration material, including:

- supported controller models and connection methods;
- button and axis mappings;
- pairing, reconnection, and device-selection steps;
- teleoperation setup and controller-side troubleshooting;
- ROS topic/message bindings, local arbitration, and launch/run configuration when selected;
- integration notes that connect a protocol contract to the robot's controller or source implementation.

## Child directories

| Directory | Purpose |
|---|---|
| [`ros/`](ros/README.md) | ROS-specific exploration, topic/message/QoS bindings, control-path evidence, safety-stop validation, and future runtime integration notes for the `CONTROLLED_ROBOT`. |

## Documentation boundaries

Transport-independent behavior contracts belong in [`../protocol-design/`](../protocol-design/). Robot hardware incidents remain with their platform-specific records under [`../husky/`](../husky/). System control authority and safety behavior remain documented under [`../../docs/architecture/safety/`](../../docs/architecture/safety/) and [`../../docs/architecture/runtime/`](../../docs/architecture/runtime/).

## Current material

The existing [Husky PS4 controller pairing record](../husky/TS-002-ps4-controller-bluetooth-pairing.md) documents the Husky 3 / Joystick 3 connection and recovery history.

The ROS exploration under [`ros/`](ros/README.md) records the live Controlled Robot control topology discovered on 2026-10-05. The Clearpath Husky A200 runs ROS 2 Jazzy; normal joystick commands pass through the existing `twist_mux`, and the existing `/husky1/platform/safety_stop` Boolean lock at priority `254` was physically verified to block joystick motion while leaving the hardware emergency-stop authority at priority `255`.

The controller integration realizes the [basic safety protocol](../protocol-design/basic-safety-protocol.md) and [Radar-side corner-proximity trigger](../protocol-design/controlled-robot-corner-trigger.md). The ROS safety binding is now identified and experimentally exercised; bridge/liveness/reconnect behavior remains to be designed before runtime implementation.
