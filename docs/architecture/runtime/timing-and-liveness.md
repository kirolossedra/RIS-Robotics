# Timing and Liveness

## Contents

- [Purpose](#purpose)
- [Known cadence](#known-cadence)
- [Open liveness policies](#open-liveness-policies)
- [Stub implication](#stub-implication)

## Purpose

Record timing and freshness assumptions that can change control meaning.

## Known cadence

The DSP acquires at approximately 12.94 Hz, classifies non-overlapping 10-frame windows, and applies a rolling vote over recent predictions. The NRF transport repeatedly advertises latched state while host serial output remains transition-oriented.

## Open liveness policies

The final system still needs explicit values/behavior for:

- maximum semantic-state age;
- BLE silence;
- RX-host process loss;
- SSH loss/reconnect;
- state resynchronization after restart;
- stale or missing distance;
- end-to-end latency acceptance.

## Stub implication

Periodic synthetic RX state can prove a consumer remains responsive at the chosen stub interval. It cannot establish the cadence, loss distribution, or latency of the real wireless producer.
