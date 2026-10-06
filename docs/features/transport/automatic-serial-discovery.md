# Automatic Serial Discovery

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Behavior](#behavior)

## Capability

Automatically select the intended NRF protocol serial endpoint when there is one unambiguous supported candidate.

## Maturity

**Implemented + software-tested.**

## Behavior

Missing or ambiguous candidates disable serial output rather than guessing. Sensing may continue, but the control path is visibly unavailable.
