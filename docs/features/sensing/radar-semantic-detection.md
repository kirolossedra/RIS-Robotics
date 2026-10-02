# Radar Semantic Detection

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Observable behavior](#observable-behavior)
- [Limitations](#limitations)

## Capability

Transform Radar/RIS observations into stabilized semantic labels used by the obstacle-state adapter.

## Maturity

**Implemented + Placeholder + Blocked for experiment control.**

The acquisition, feature pipeline, inference adapter, and rolling vote exist, but the current CNN-LSTM artifact is not the trained experiment detector.

## Observable behavior

The current UI/control interface exposes person, robot, and nothing labels on the expected cadence.

## Limitations

Placeholder label mapping validates integration shape only. It does not establish detection accuracy, false-alarm behavior, or valid corridor semantics.
