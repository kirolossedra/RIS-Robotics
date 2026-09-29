# System Documentation

**Role:** canonical cross-subsystem documentation for RIS-Robotics.  
**Audit basis:** implementation and validation evidence present on `main` on 2026-09-28, immediately before this documentation overhaul.  
**Rule:** intended architecture is never presented as implemented behavior.

## Contents

- [Purpose](#purpose)
- [Status vocabulary](#status-vocabulary)
- [Documentation map](#documentation-map)
- [Source-of-truth hierarchy](#source-of-truth-hierarchy)
- [Current system boundary](#current-system-boundary)
- [Known open system decisions](#known-open-system-decisions)
- [Maintenance rules](#maintenance-rules)

## Purpose

This directory owns the system-wide view that no single subsystem README can provide. It connects sensing, DSP, serial transport, BLE firmware, robot-side transport, and motion arbitration while preserving each subsystem's own implementation documentation.

## Status vocabulary

| Status | Meaning |
|---|---|
| **Implemented** | Code/configuration exists in the repository. |
| **Validated** | The stated behavior has direct test or hardware evidence. |
| **Blocked** | Implementation exists but cannot be treated as experiment-ready because a prerequisite is missing. |
| **Design only** | Architecture/decision exists, but no corresponding implementation is present. |
| **TBD** | The project has not selected the mechanism/value yet. |
| **Historical** | Useful evidence of past work, not a statement of current architecture. |

An item can be both implemented and blocked, or implemented and not yet validated. These are different dimensions.

## Documentation map

- [`architecture.md`](architecture.md) — system topology, boundaries, responsibilities, and non-goals.
- [`interfaces.md`](interfaces.md) — exact inter-subsystem contracts and which contracts are still proposals.
- [`runtime-and-state.md`](runtime-and-state.md) — state ownership, latches, transitions, and STOP gating.
- [`implementation-status.md`](implementation-status.md) — current maturity ledger with implementation evidence.
- [`validation.md`](validation.md) — verification/validation evidence and remaining proof gaps.
- [`failure-modes-and-safety.md`](failure-modes-and-safety.md) — known failures, current behavior, unresolved policies, and safety boundaries.
- [`integration-plan.md`](integration-plan.md) — dependency-ordered work needed to reach the complete demonstration.
- [`system.md`](system.md) — legacy entry point retained for old links; points here and to `architecture.md`.
- [`control-signal-path.md`](control-signal-path.md) — legacy entry point retained for old links; points to the split runtime/interface/integration records.

Subsystem detail remains in [`../dsp/`](../dsp/), [`../firmware/`](../firmware/), and [`../robotics/`](../robotics/). Architecture rationale remains in [`../decision-logs/`](../decision-logs/).

## Source-of-truth hierarchy

When documents disagree, resolve the disagreement in this order:

1. **Current implementation and configuration** — what the code actually does.
2. **Dated validation evidence** — what has actually been observed or tested.
3. **Accepted decision records** — what the team has chosen to build.
4. **This system documentation** — synthesized current state and cross-boundary contracts.
5. **Session logs and superseded records** — historical evidence only.

A decision record can be accepted while its implementation is still pending. A historical session can truthfully describe an earlier state without being current.

## Current system boundary

The repository is complete and physically validated through the NRF BLE transport. The live DSP has a coded serial integration path, but experiment control is deliberately blocked by placeholder inference. The downstream Jackal bridge, ROS arbiter, and distance gate remain unimplemented.

```text
validated hardware:
host UART -> NRF TX -> BLE S=8 -> NRF RX -> host UART

target system:
Radar/RIS -> DSP -> serial -> NRF TX -> BLE -> NRF RX -> serial
          -> SSH/ROS bridge -> local distance-gated STOP -> Jackal
```

## Known open system decisions

- Trained detector artifact and final output-label mapping.
- Distance-to-corner source/method.
- `DISTANCE_THRESHOLD` value and calibration process.
- Jackal-side bridge implementation details beyond the accepted persistent-SSH architecture.
- Exact ROS arbitration mechanism/topic wiring on the Jackal.
- Explicit communication-loss policy for BLE/serial/SSH and stale state.

## Maintenance rules

- Update [`implementation-status.md`](implementation-status.md) when a subsystem crosses an implementation or validation boundary.
- Add validation claims only when a reproducible test or dated evidence exists.
- Keep pending behavior visibly pending; do not describe planned SSH/ROS logic in present tense.
- Do not duplicate DSP mathematics or firmware internals here; link to the owning subsystem.
- Preserve historical session records, but repair current docs when implementation supersedes them.
- Keep every system Markdown file indexed here and give every system Markdown file its own contents section.
