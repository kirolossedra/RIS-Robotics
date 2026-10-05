# Robotics Protocol Design

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Documentation boundaries](#documentation-boundaries)
- [Current material](#current-material)
- [Assumptions](#assumptions)
- [AsyncAPI](#asyncapi)

## Purpose

This directory owns transport-independent protocol contracts and behavior algorithms: what a signal means, which signal takes precedence, and how protocol states change.

## Scope

Use this area for specifications and algorithms concerning:

- semantic messages such as Radar `OBS` and `CLR`;
- state transitions, command precedence, and sender/receiver behavior;
- timeout, malformed-input, reconnect, and failure semantics that are part of a protocol contract.

Protocol design is not the ROS implementation. ROS topics, message types, controller integration, and runtime code belong under [`../controller/`](../controller/) or the implementing source package.

## Documentation boundaries

System-wide architecture and interaction authority remains under [`../../docs/architecture/`](../../docs/architecture/). Accepted design rationale belongs in [`../../docs/decisions/`](../../docs/decisions/). This directory records robot-side protocol details and points to those canonical records instead of duplicating them.

## Current material

- [Basic safety protocol](basic-safety-protocol.md) — Radar `OBS` takes precedence over the joystick command; includes pseudocode and flowcharts.
- [AsyncAPI contract](basic-safety-protocol.asyncapi.yaml) — machine-readable logical Radar safety-state event contract.
- [Controlled Robot corner-proximity trigger](controlled-robot-corner-trigger.md) — Radar-side slant-range projection and proposed 2.0 m trigger, with speed/footprint analysis, pseudocode, Mermaid diagrams, and explicit limitations.
- [Corner-proximity AsyncAPI contract](controlled-robot-corner-trigger.asyncapi.yaml) — machine-readable trigger/clear event addressed to `CONTROLLED_ROBOT`.
- Canonical implemented transport details remain in the [system interfaces](../../docs/architecture/interactions/interfaces.md).

## Assumptions

Every protocol document must state its assumptions in that document and in its machine-readable contract. Protocol assumptions are not implementation evidence: the corner trigger's Husky A200 speed/footprint comparison supports a preliminary 2.0 m design point, while stopping-distance validation remains open.

## AsyncAPI

AsyncAPI describes message-driven contracts independently from the runtime implementation. This repository uses it for the logical event contract; it does not select a ROS topic or replace the controller's native ROS interfaces. AsyncAPI 3.1.0 also defines a ROS 2 binding, but this contract does not use that binding until the robot's ROS version and concrete interface are selected. See the [AsyncAPI 3.1.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.1.0) and [3.1.0 release notes](https://www.asyncapi.com/blog/release-notes-3.1.0).
