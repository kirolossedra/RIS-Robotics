# Stubs and Simulation Boundaries

## Contents

- [Purpose](#purpose)
- [Status model](#status-model)
- [Known stubs and substitutes](#known-stubs-and-substitutes)
- [Rules](#rules)

## Purpose

RIS-Robotics intentionally uses stubs to decouple integration stages. This document prevents a successful stub-driven path from being mistaken for validation of the real producer it replaces.

## Status model

- **Stub**: deliberate controllable substitute for an interface producer.
- **Placeholder**: temporary production-shaped implementation with invalid experiment semantics.
- **Design only**: no implementation yet.

These labels are not interchangeable.

## Known stubs and substitutes

| Mechanism | Type | Substitutes for | Allowed proof | Does not prove |
|---|---|---|---|---|
| RX Forced CLR / Forced OBS modes | **Stub** | natural BLE receive-state input at the RX processing boundary | RX dedup/output path, mode control, indicators, downstream serial integration when exercised | over-air reception, RF reliability, natural packet filtering |
| temporary local `ifxradarsdk` test double used in the 2026-09-28 DSP test environment | **Test stub, external to repo** | vendor SDK import/hardware boundary | hardware-free DSP logic tests | radar hardware behavior or SDK integration |
| current CNN-LSTM activity model mapped to person/robot/nothing | **Placeholder** | trained experiment detector | interface shape and UI/control integration only | detection accuracy or valid corridor semantics |
| future serial->SSH bridge / ROS arbiter | **Design only** | nothing; implementation absent | architecture review only | runtime behavior |

## Rules

- Stub activation must be visible.
- Natural and stub input must never be accepted simultaneously unless explicitly designed and validated.
- Stub-driven tests must name the substituted boundary.
- Feature maturity for the real path stays unchanged after a stub-only pass.
- A placeholder may not drive experiment control merely because downstream integration works.
