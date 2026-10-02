# Obstacle-State Generation

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Behavior](#behavior)

## Capability

Map stable semantic labels to a transport-neutral `CLEAR` / `OBSTACLE` state and emit transition-oriented `CLR`/`OBS`.

## Maturity

**Implemented + software-tested.** Experiment use is still blocked upstream by placeholder inference.

## Behavior

Person/robot map to obstacle; nothing maps to clear; unknown/fault holds the previous semantic state instead of manufacturing clear.
