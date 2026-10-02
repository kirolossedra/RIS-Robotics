# RX Reception Stubs

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Modes](#modes)
- [What this feature proves](#what-this-feature-proves)
- [What it does not prove](#what-it-does-not-prove)

## Capability

Deliberately substitute synthetic RX state for natural over-air reception so RX-side processing and later integration can be exercised independently.

## Maturity

**Implemented + Stub + partially hardware-validated.**

## Modes

The RX receive source cycles through:

```text
Natural -> Forced CLR -> Forced OBS -> Natural
```

Visual mode indication is implemented.

## What this feature proves

A stub-driven test may validate mode switching, indicators, RX dedup/output behavior, and downstream consumers at the RX processing boundary.

## What it does not prove

It does not prove natural BLE packet reception, RF reliability, range, packet-loss behavior, or the real upstream producer.

See [`../../architecture/runtime/stubs-and-simulation.md`](../../architecture/runtime/stubs-and-simulation.md).
