# ROS Controller Integration

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Current documents](#current-documents)

## Purpose

This directory owns ROS-specific exploration, bindings, runtime observations, and implementation notes for the `CONTROLLED_ROBOT` controller path.

It records how the transport-independent RIS safety semantics are bound to the robot's existing ROS control stack without changing the architectural rule that final motion authority remains local to the `CONTROLLED_ROBOT`.

## Scope

Use this directory for:

- discovery of the installed ROS distribution and runtime topology;
- ROS topic, message, QoS, mux, and controller bindings;
- verification of joystick-to-base command flow;
- verification of software safety-stop behavior;
- ROS-side observations needed before implementing the RIS-to-robot bridge;
- future ROS launch/runtime integration notes when implementation is selected.

Transport-independent `OBS` / `CLR` behavior remains in [`../../protocol-design/`](../../protocol-design/). Hardware-specific incidents remain under the owning robot directory. Canonical control-authority and failure-policy documentation remains under [`../../../docs/architecture/safety/`](../../../docs/architecture/safety/).

## Current documents

- [`exploration.md`](exploration.md) — recorded 2026-10-05 exploration of the Clearpath Husky A200 ROS 2 Jazzy control path, existing `twist_mux` safety locks, live STOP/release experiment, and implications for RIS integration.
