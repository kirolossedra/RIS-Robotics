# Robotics Controller and Integration

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Documentation boundaries](#documentation-boundaries)
- [Current material](#current-material)

## Purpose

This directory owns robot-side controller setup and integration documentation, including how protocol behavior is bound to the ROS control stack. Runtime implementations belong in their actual source packages.

## Scope

Use this area for controller and robot-integration material, including:

- supported controller models and connection methods;
- button and axis mappings;
- pairing, reconnection, and device-selection steps;
- teleoperation setup and controller-side troubleshooting.
- ROS topic/message bindings, local arbitration, and launch/run configuration when selected.
- integration notes that connect a protocol contract to the robot's controller or source implementation.

## Documentation boundaries

Transport-independent behavior contracts belong in [`../protocol-design/`](../protocol-design/). Robot hardware incidents remain with their platform-specific records under [`../husky/`](../husky/). System control authority and safety behavior remain documented under [`../../docs/architecture/safety/`](../../docs/architecture/safety/) and [`../../docs/architecture/runtime/`](../../docs/architecture/runtime/).

## Current material

The existing [Husky PS4 controller pairing record](../husky/TS-002-ps4-controller-bluetooth-pairing.md) documents the Husky 3 / Joystick 3 connection and recovery history. No standalone controller configuration or ROS integration guide has been added here yet.

The controller integration realizes the [basic safety protocol](../protocol-design/basic-safety-protocol.md) and [Radar-side corner-proximity trigger](../protocol-design/controlled-robot-corner-trigger.md). The ROS topic and implementation remain unselected.
