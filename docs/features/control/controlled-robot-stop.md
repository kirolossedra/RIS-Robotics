# Controlled Robot STOP

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Target behavior](#target-behavior)
- [Dependencies](#dependencies)

## Capability

Give a locally enforced STOP authority precedence over normal Controlled Robot teleoperation.

## Maturity

**Design only.**

## Target behavior

A robot-local arbiter prevents normal velocity commands from overriding an asserted STOP.

## Dependencies

Persistent RX-host-to-robot transport, a selected ROS arbitration interface, explicit liveness/failure policy, and independent STOP assertion/release validation.
