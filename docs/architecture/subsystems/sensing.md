# Sensing Subsystem

## Contents

- [Responsibility](#responsibility)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Maturity](#maturity)

## Responsibility

Observe the physical conflicting-corridor scene through the Radar/RIS setup and provide radar frames to the DSP acquisition boundary.

## Inputs

- physical motion from people and the `DUMMY_ROBOT`;
- current Radar/RIS physical configuration.

## Outputs

Raw radar frames consumed by the DSP implementation.

## Maturity

Physical sensing/acquisition exists. Experiment-valid semantic detection remains dependent on the trained detector represented downstream in the DSP subsystem.
