# Distance-Gated STOP

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Target rule](#target-rule)
- [Open decisions](#open-decisions)

## Capability

Apply the higher-priority STOP when the Radar-side corner-proximity protocol triggers for the `CONTROLLED_ROBOT`. The Radar computes the trigger from its own range/height observation; the `CONTROLLED_ROBOT` is the event recipient and the `DUMMY_ROBOT` is never commanded by this protocol.

## Maturity

**Design only.** The Radar-side geometry and 2.0 m proposed threshold are documented. Range-to-reference calibration, release semantics, message delivery, local ROS arbitration, and stopping-distance validation remain incomplete.

## Target rule

```text
Radar track identifies CONTROLLED_ROBOT
d = sqrt(r^2 - (h - z)^2)
d <= 2.0 m -> TRIGGER to CONTROLLED_ROBOT -> local STOP precedence
```

The current physical binding is Clearpath Husky A200: 990 mm long, 670 mm wide, with documented maximum speed 1 m/s. At a 2.0 m center-reference threshold, the straight-ahead front edge is approximately 1.505 m from the corner. This supports an initial geometry comparison but does not prove stopping performance; the [protocol document](../../../robotics/protocol-design/controlled-robot-corner-trigger.md) defines the validation inequality and assumptions.

## Open decisions

Radar target association/reference-point calibration; range uncertainty; sample freshness; clear threshold/hysteresis; configured speed enforcement; end-to-end trigger latency; minimum braking deceleration; and supervised stopping-distance evidence.
