# RIS Robotics — System Design (Legacy Entry Point)

## Contents

- [Current canonical documentation](#current-canonical-documentation)
- [Current state summary](#current-state-summary)

## Current canonical documentation

This filename is retained so historical links do not break. The former monolithic system description has been split into maintained system records:

- [`README.md`](README.md) — system documentation control center.
- [`architecture.md`](architecture.md) — topology, responsibilities, current versus target architecture.
- [`implementation-status.md`](implementation-status.md) — what is implemented, validated, blocked, design-only, or TBD.
- [`interfaces.md`](interfaces.md) — exact cross-subsystem contracts.
- [`runtime-and-state.md`](runtime-and-state.md) — state and gating semantics.
- [`validation.md`](validation.md) — evidence.
- [`failure-modes-and-safety.md`](failure-modes-and-safety.md) — failures and unresolved policies.
- [`integration-plan.md`](integration-plan.md) — remaining work.

## Current state summary

The repository is validated through the nRF52833 TX -> BLE Coded S=8 -> RX link. DSP serial integration exists in code but experiment actuation is blocked by placeholder inference. The Controlled Robot serial/SSH bridge, ROS arbitration, and distance-to-corner gate are not yet implemented.
