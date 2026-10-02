# TX Manual State Injection

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Boundary substituted](#boundary-substituted)
- [Allowed proof](#allowed-proof)
- [Not proven](#not-proven)

## Capability

Use Transceiver Button 3 while in TX role to set the same shared `CLR`/`OBS` state latch used by serial input, allowing the wireless/downstream chain to be exercised without a live DSP producer.

## Maturity

**Implemented + integration stub/test input + hardware-exercised.**

## Boundary substituted

The manual input substitutes for the upstream DSP-to-TX serial producer at the TX state-latch boundary. It does not create a second production state path; both inputs converge on the same latch.

## Allowed proof

It can support validation of TX state changes, BLE advertising, RX behavior, and downstream consumers when those boundaries are included in the test.

## Not proven

It does not validate semantic detection, the DSP obstacle-state adapter, automatic serial discovery, the physical DSP-to-TX serial boundary, or experiment-valid classifier output.

See [`../../architecture/runtime/stubs-and-simulation.md`](../../architecture/runtime/stubs-and-simulation.md).
