# Distance-Gated STOP

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Target rule](#target-rule)
- [Open decisions](#open-decisions)

## Capability

Apply the higher-priority STOP only when unsafe corridor state and Controlled Robot proximity to the corner both require intervention.

## Maturity

**Design only + TBD dependencies.**

## Target rule

```text
unsafe AND distance_to_corner <= DISTANCE_THRESHOLD -> STOP
```

## Open decisions

Distance source, units/update-rate contract, validity/staleness policy, calibration method, and `DISTANCE_THRESHOLD`.
