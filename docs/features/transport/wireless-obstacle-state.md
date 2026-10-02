# Wireless Obstacle-State Transport

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Contract](#contract)
- [Evidence](#evidence)

## Capability

Transport compact `OBS`/`CLR` state from TX host to RX host through the shared nRF52833 Transceiver firmware.

## Maturity

**Implemented + hardware-validated for the default Coded S=8 two-board path.**

## Contract

Repeated wireless advertisements are deduplicated into transition-oriented RX serial output.

## Evidence

See [`../../../firmware/validation/2026-09-28-two-board-smoke-test.md`](../../../firmware/validation/2026-09-28-two-board-smoke-test.md).
