# Data Flow

## Contents

- [Purpose](#purpose)
- [Representation flow](#representation-flow)
- [Authority boundary](#authority-boundary)

## Purpose

Track how representation changes as information moves from sensing to action.

## Representation flow

```text
physical scene
 -> complex radar samples
 -> range/Doppler/angle feature maps
 -> model label + score
 -> rolling-voted semantic label
 -> CLEAR / OBSTACLE
 -> ASCII CLR / OBS
 -> BLE state byte
 -> ASCII CLR / OBS
 -> robot safety state [design only]
 -> final motion command [design only]
```

Each reduction is intentional. Raw sensing data do not cross the NRF transport boundary.

## Authority boundary

Data transport ends before final motion policy. STOP precedence belongs to the Controlled Robot-local arbitration layer.
