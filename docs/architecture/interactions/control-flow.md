# Control Signal Path (Legacy Entry Point)

## Contents

- [Canonical records](#canonical-records)
- [Current path](#current-path)

## Canonical records

This filename is retained for historical references. The old integration-plan content was split because it mixed implemented behavior with future architecture.

- Contract details: [`interfaces.md`](interfaces.md)
- Runtime/state semantics: [`runtime-and-state.md`](../runtime/state-machines.md)
- Current implementation maturity: [`implementation-status.md`](../system/current-state.md)
- Remaining dependency-ordered work: [`integration-plan.md`](../system/integration-plan.md)
- Failure behavior: [`failure-modes-and-safety.md`](../safety/failure-modes.md)

## Current path

```text
IMPLEMENTED:
Radar/DSP -> voted label -> obstacle adapter -> serial writer
           -> NRF TX -> BLE -> NRF RX -> serial

BLOCKED / NOT YET INTEGRATED:
placeholder model prevents experiment-valid DSP control

DESIGN ONLY:
Radar slant range + height -> corner-proximity protocol (d <= 2.0 m)
                           -> trigger to CONTROLLED_ROBOT
RX serial -> persistent SSH -> Controlled Robot ROS arbiter
          -> trigger/OBS STOP precedence -> Controlled Robot

OPEN:
Radar target reference/calibration, clear hysteresis, event transport,
trigger-to-stop latency, and stopping-distance evidence
```
