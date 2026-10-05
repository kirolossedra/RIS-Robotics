# Features

## Contents

- [Purpose](#purpose)
- [Feature rule](#feature-rule)
- [Feature map](#feature-map)
- [Maturity rule](#maturity-rule)

## Purpose

Features describe **capabilities** visible to an operator, integrator, or downstream subsystem. They answer what the system can do without becoming implementation or architecture documents.

## Feature rule

Each feature states:

- capability and trigger;
- observable behavior;
- maturity;
- architecture dependencies;
- governing decisions;
- validation evidence;
- stub/placeholder limitations when applicable.

## Feature map

The feature tree is divided by capability domain. Each immediate child directory owns its local feature index.

| Directory | Capability boundary | What belongs there | Recursive index |
|---|---|---|---|
| [`sensing/`](sensing/) | Radar-side interpretation | Features that turn sensor data into semantic detections | [`sensing/README.md`](sensing/README.md) |
| [`transport/`](transport/) | State movement between subsystems | Serial discovery/output, wireless obstacle state, runtime Transceiver modes, and receive stubs | [`transport/README.md`](transport/README.md) |
| [`control/`](control/) | Control-state generation and actuation semantics | Obstacle-state generation, Controlled Robot STOP, and distance-gated STOP behavior | [`control/README.md`](control/README.md) |

### Sensing

- [`sensing/radar-semantic-detection.md`](sensing/radar-semantic-detection.md)

### Transport

- [`transport/automatic-serial-discovery.md`](transport/automatic-serial-discovery.md)
- [`transport/wireless-obstacle-state.md`](transport/wireless-obstacle-state.md)
- [`transport/tx-manual-state-injection.md`](transport/tx-manual-state-injection.md)
- [`transport/runtime-transceiver-modes.md`](transport/runtime-transceiver-modes.md)
- [`transport/rx-reception-stubs.md`](transport/rx-reception-stubs.md)

### Control

- [`control/obstacle-state-generation.md`](control/obstacle-state-generation.md)
- [`control/controlled-robot-stop.md`](control/controlled-robot-stop.md)
- [`control/distance-gated-stop.md`](control/distance-gated-stop.md)

## Maturity rule

A feature inherits the weakest maturity of the real dependencies required for the claim. Stub-only validation cannot promote a real-path feature to validated.
