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
| TX Button-3 manual CLR/OBS injection | **Integration stub / test input** | DSP serial producer at the TX state-latch boundary | TX latch, advertising, BLE/RX path and downstream behavior without live DSP | DSP classification, serial discovery/writer, live DSP-to-TX boundary |
| RX Forced CLR / Forced OBS modes | **Stub** | natural BLE receive-state input at the RX processing boundary | RX dedup/output path, mode control, indicators, downstream serial integration when exercised | over-air reception, RF reliability, natural packet filtering |
| `FakeRadar`, `FakeGUI`, `FakeClassifier` | **Unit-test doubles** | radar, GUI, and model boundaries in DSP tests | deterministic DSP lifecycle/voting/windowing behavior | real radar, GUI timing, trained-model behavior |
| injected `FakeStream` in serial integration tests | **Unit-test double** | physical serial stream | framing, failure/retry, transition semantics | USB/UART discovery or physical TX behavior |
| temporary local `ifxradarsdk` test double used in the 2026-09-28 DSP test environment | **Test stub, external to repo** | vendor SDK import/hardware boundary | hardware-free DSP logic tests | radar hardware behavior or SDK integration |
| current CNN-LSTM activity model mapped to person/robot/nothing | **Placeholder** | trained experiment detector | interface shape and UI/control integration only | detection accuracy or valid corridor semantics |
| future serial->SSH bridge / ROS arbiter | **Design only** | nothing; implementation absent | architecture review only | runtime behavior |

## Rules

- Stub activation must be visible.
- Manual integration injection that bypasses an upstream producer is treated as a stub/test input for maturity accounting even when it shares the production state latch.
- Natural and stub input must never be accepted simultaneously unless explicitly designed and validated.
- Stub-driven tests must name the substituted boundary.
- Feature maturity for the real path stays unchanged after a stub-only pass.
- A placeholder may not drive experiment control merely because downstream integration works.
