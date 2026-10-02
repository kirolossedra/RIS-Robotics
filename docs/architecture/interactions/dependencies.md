# Dependencies

## Contents

- [Purpose](#purpose)
- [Dependency graph](#dependency-graph)
- [Change-impact rules](#change-impact-rules)
- [Stub dependencies](#stub-dependencies)

## Purpose

This document makes cross-cutting change impact explicit so a local edit does not silently invalidate another subsystem or its evidence.

## Dependency graph

```mermaid
flowchart LR
    MODEL[Detector label contract] --> ADAPTER[Obstacle-state adapter]
    ADAPTER --> SERIAL[OBS/CLR serial contract]
    SERIAL --> TX[TX parser/latch]
    TX --> PACKET[BLE service-data contract]
    PACKET --> RX[RX validation/dedup]
    RX --> HOST[RX host interface]
    HOST --> BRIDGE[Controlled Robot bridge - design only]
    BRIDGE --> ARB[Local arbiter - design only]
    DIST[Distance source/threshold - TBD] --> ARB

    SERIAL --> STEST[Serial integration tests]
    PACKET --> BTEST[Two-board validation]
    RX --> STUB[RX reception stubs]
```

## Change-impact rules

| Dependency changed | Minimum affected areas |
|---|---|
| model output labels | DSP adapter, feature docs, trained-model validation |
| `OBS`/`CLR` framing | DSP writer, TX parser, interface docs, serial tests |
| BLE UUID/version/state byte | TX/RX firmware, protocol tests, two-board validation |
| role/PHY runtime semantics | firmware, operations, stub behavior, hardware validation |
| Controlled Robot ROS interface | bridge, arbiter, control-flow docs, failure/liveness policy |
| distance contract | runtime state, arbiter, safety policy, end-to-end validation |

## Stub dependencies

A stub depends on the downstream interface it exercises but **does not satisfy** the dependency on the real upstream producer. For example, forced RX `OBS` can validate RX serial/downstream handling but cannot validate over-air packet reception.
