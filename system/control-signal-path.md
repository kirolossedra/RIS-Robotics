# Control Signal Path (Legacy Entry Point)

## Contents

- [Canonical records](#canonical-records)
- [Current path](#current-path)

## Canonical records

This filename is retained for historical references. The old integration-plan content was split because it mixed implemented behavior with future architecture.

- Contract details: [`interfaces.md`](interfaces.md)
- Runtime/state semantics: [`runtime-and-state.md`](runtime-and-state.md)
- Current implementation maturity: [`implementation-status.md`](implementation-status.md)
- Remaining dependency-ordered work: [`integration-plan.md`](integration-plan.md)
- Failure behavior: [`failure-modes-and-safety.md`](failure-modes-and-safety.md)

## Current path

```text
IMPLEMENTED:
Radar/DSP -> voted label -> obstacle adapter -> serial writer
           -> NRF TX -> BLE -> NRF RX -> serial

BLOCKED / NOT YET INTEGRATED:
placeholder model prevents experiment-valid DSP control

DESIGN ONLY:
RX serial -> persistent SSH -> Controlled Robot ROS arbiter
          -> distance-gated STOP -> Controlled Robot

TBD:
distance-to-corner source and DISTANCE_THRESHOLD
```
