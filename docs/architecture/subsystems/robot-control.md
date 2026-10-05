# Robot Control Subsystem

## Contents

- [Responsibility](#responsibility)
- [Target path](#target-path)
- [Authority](#authority)
- [Maturity](#maturity)

## Responsibility

Deliver the received semantic state to the `CONTROLLED_ROBOT` and enforce STOP precedence locally.

## Target path

```text
RX serial
 -> Controlled Robot-side host
 -> persistent SSH transport
 -> robot-local ROS safety input
 -> local command arbiter
 -> Radar corner-proximity trigger / safety STOP
 -> base controller
```

## Authority

The final motion authority is local to the Controlled Robot. Network arrival order is not a safety policy.

## Maturity

The bridge, ROS arbitration, and Radar-side corner-proximity trigger are **Design only**. The protocol proposes a 2.0 m threshold at 1 m/s for Husky A200, but reference-point calibration, event delivery, release behavior, latency, and stopping-distance validation remain open.
