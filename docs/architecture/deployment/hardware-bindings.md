# Hardware Bindings

## Contents

- [Purpose](#purpose)
- [Current bindings](#current-bindings)
- [Binding rule](#binding-rule)

## Purpose

Keep replaceable product choices out of stable architecture names.

## Current bindings

| Architectural role/component | Current binding |
|---|---|
| `DUMMY_ROBOT` | Clearpath Husky A200 |
| `CONTROLLED_ROBOT` | Clearpath Husky A200 |
| TX Transceiver | Nordic nRF52833 DK |
| RX Transceiver | Nordic nRF52833 DK |
| Radar | current Infineon FMCW radar used by the DSP acquisition path |
| central sensing host | experiment laptop/PC running the DSP pipeline |

## Binding rule

Changing a binding normally requires platform-specific integration and validation updates, not renaming the architecture. See [`../../decisions/robot-runtime-0003-robot-role-abstraction-and-hardware-binding.md`](../../decisions/robot-runtime-0003-robot-role-abstraction-and-hardware-binding.md).

The two roles may use the same Husky A200 model, but refer to separate physical robot instances when both are present in the experiment.
