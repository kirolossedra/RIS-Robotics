# Implementation Status

## Contents

- [Purpose](#purpose)
- [Maturity ledger](#maturity-ledger)
- [Implemented but blocked](#implemented-but-blocked)
- [Design-only areas](#design-only-areas)
- [TBD items](#tbd-items)
- [Definition of system-ready](#definition-of-system-ready)

## Purpose

This is the repository-wide maturity ledger. It answers two separate questions for every block: **does implementation exist?** and **has the required behavior been validated?**

## Maturity ledger

| Block | Implementation | Validation | Current interpretation | Evidence |
|---|---|---|---|---|
| Radar acquisition | Implemented | Existing runtime/test evidence | Available subsystem | `dsp/collect_data_realtime.py` |
| Range/Doppler/Capon feature construction | Implemented | Software checks exist | Available subsystem | `dsp/realtime_classifier.py`, `dsp/docs/` |
| CNN-LSTM adapter | Implemented | Structural/test coverage | **Blocked for experiment semantics by placeholder model** | `PLACEHOLDER_MODE = True` |
| Rolling vote | Implemented | Software-tested | Available, no hysteresis | `dsp/tests/` |
| Obstacle-state adapter | Implemented | Hardware-free tested | Available | `dsp/integration/obstacle_state.py` |
| Serial auto-discovery | Implemented | Metadata/test coverage | Available; ambiguity disables output | `dsp/integration/serial_discovery.py` |
| Serial state writer | Implemented | Hardware-free tested | Live-DSP->TX hardware boundary not yet proven | `dsp/integration/serial_output.py` |
| Shared transceiver image | Implemented | Correct-target boot proven | Available | `firmware/transceiver/` |
| Runtime TX/RX role logic | Implemented | Partial hardware use | Dedicated Button-2 role-switch validation remains open | firmware + validation records |
| Coded S=8 transport | Implemented | **Two-board smoke PASS** | Validated for same-PHY OBS/CLR transport | two-board validation |
| LE 1M runtime mode | Implemented | Dedicated coordinated switch test open | Implemented, not fully hardware-validated | firmware |
| RX duplicate suppression | Implemented | **Two-board smoke PASS** | Validated for repeated OBS/CLR episode | two-board validation |
| RX JSONL logger | Implemented | Dedicated hardware run open | Implemented, not hardware-validated | `firmware/tools/rx_logger.py` |
| Jackal Ethernet/SSH reachability | Operational work documented | Not a production bridge | Supporting capability only | `robotics/`, decision log |
| Persistent serial->SSH bridge | Not implemented | None | Design only | `robot-ros-0001` |
| ROS safety arbitration | Not implemented | None | Design only | `robot-ros-0001` |
| Distance-to-corner source | Not selected | None | TBD | system/decision docs |
| Distance threshold | Not selected | None | TBD | system/decision docs |
| End-to-end sensing->STOP | Not implemented as one chain | None | Not system-ready | cross-system |

## Implemented but blocked

### Experiment-valid DSP control

The serial boundary is real code, but the classifier is still intentionally in placeholder mode. The default guard prevents serial output from being used as though placeholder labels were valid corridor detections. The next step is not to remove the guard; it is to install and validate the correct detector and label contract.

### Full Transceiver feature set

The single image and both PHY paths exist. The 2026-09-28 two-board smoke test validates S=8 `OBS`/`CLR` transport and duplicate suppression, but it does not close every firmware validation item: hardware Button-1/2 behavior, coordinated PHY switching, logger JSONL, range/reliability, and longer-run behavior remain open.

## Design-only areas

The accepted persistent-SSH bridge and local ROS arbitration are architecture decisions only. The repository contains no implemented bridge, ROS command-arbitration node/configuration, or distance gate.

## TBD items

- trained detector artifact and authoritative label mapping;
- distance-to-corner mechanism;
- `DISTANCE_THRESHOLD`;
- robot-side ROS interface and arbiter implementation details;
- reconnect/resynchronization policy across serial/SSH;
- communication-loss and stale-distance policy;
- experiment acceptance thresholds for latency/reliability.

## Definition of system-ready

The project should not be described as end-to-end ready until the experiment-valid detector, live DSP->TX boundary, chosen NRF transport, Jackal bridge, local arbitration, distance gate, failure policies, and full-chain validation have all been completed with evidence.
