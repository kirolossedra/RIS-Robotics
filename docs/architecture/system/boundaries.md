# System Boundaries

## Contents

- [Purpose](#purpose)
- [Inside the system](#inside-the-system)
- [Outside the system](#outside-the-system)
- [Robot-role boundary](#robot-role-boundary)
- [Research boundary](#research-boundary)

## Purpose

This document prevents implementation scope, research scope, and hardware availability from being mistaken for the architecture itself.

## Inside the system

The architecture covers:

```text
DUMMY_ROBOT physical stimulus
    -> Radar/RIS sensing
    -> DSP semantic reduction
    -> OBS/CLR serial boundary
    -> NRF wireless transport
    -> RX host boundary
    -> CONTROLLED_ROBOT bridge/arbitration [design only]
    -> distance-gated STOP [design only/TBD]
```

## Outside the system

The current architecture does not require autonomous navigation, SLAM, path planning, or general-purpose multi-robot coordination.

The software STOP is not a replacement for the physical emergency stop or supervised laboratory procedure.

## Robot-role boundary

The stable architecture names are `DUMMY_ROBOT` and `CONTROLLED_ROBOT`. Current hardware bindings are deployment details documented under [`../deployment/hardware-bindings.md`](../deployment/hardware-bindings.md).

## Research boundary

Radar/RIS sensing is the primary research contribution. The robotics path demonstrates a controlled response to the sensed condition without turning the mobile platform into the research problem itself.
