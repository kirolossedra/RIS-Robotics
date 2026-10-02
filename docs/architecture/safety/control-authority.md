# Control Authority

## Contents

- [Authorities](#authorities)
- [Gating context](#gating-context)
- [Locality rule](#locality-rule)
- [Physical safety boundary](#physical-safety-boundary)

## Authorities

The target Controlled Robot has two logical motion authorities:

1. normal teleoperation / `cmd_vel`;
2. higher-priority STOP.

## Gating context

Distance-to-corner is context used by the STOP policy. It is not a third motion authority.

## Locality rule

STOP precedence must be enforced locally on the Controlled Robot. Message arrival order across serial/BLE/SSH is not a priority mechanism.

## Physical safety boundary

The software STOP remains an experiment mechanism. The physical emergency stop and supervised laboratory procedure remain independent safety controls.
