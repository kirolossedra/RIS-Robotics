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
 -> distance-gated STOP
 -> base controller
```

## Authority

The final motion authority is local to the Controlled Robot. Network arrival order is not a safety policy.

## Maturity

The bridge, ROS arbitration, and distance gate are currently **Design only**. The distance source and threshold remain **TBD**.
