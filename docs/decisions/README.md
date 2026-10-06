# Decision Logs

This directory records significant design decisions for the RIS Robotics experiment.

## Contents

- [Naming convention](#naming-convention)
- [Index](#index)
- [Experiment context](#experiment-context)

## Naming convention

Every decision file follows the RIS decision identity format:

```text
<subsystem>-<environment>-<NNNN>-<decision-name>.md
```

- **Subsystem** comes first: the actual subsystem the decision belongs to (e.g. `ble`, `robot`), taken from repository evidence. No abbreviations or aliases may be invented.
- **Environment** comes second: the context in which the decision primarily applies (e.g. `runtime`, `ros`, `hardware`), using only terminology already supported by the repository.
- **Four-digit sequence** comes third (e.g. `0001`). The counter is local to that exact subsystem-environment combination: each pair starts its own sequence at `0001`. There is no repository-global counter.
- **Descriptive kebab-case name** comes last (e.g. `role-selection`). It explains the decision and is not part of the identity sequence.
- No additional taxonomy layer may be inserted into the filename without an explicit decision, and no acronym or category may be invented merely to make a filename fit.
- Ambiguous classification must be surfaced rather than guessed.

Examples (naming syntax only, not new records):

```text
ble-runtime-0001-role-selection.md
ble-runtime-0002-phy-switching.md

robot-ros-0001-high-priority-stop-command.md
robot-ros-0002-distance-to-corner-gating.md

robot-runtime-0001-stop-clear-state-handling.md
robot-hardware-0001-jackal-platform-selection.md
```

Each record carries its authoritative `ID` in its heading and preserves its legacy `DL-###` identifier as `Previous ID` metadata. Git history plus that metadata keeps the migration reconstructable.

## Index

| ID | Decision | State | Previous ID |
|---|---|---|---|
| `ble-runtime-0001` | [Wi-Fi to BLE communication](ble-runtime-0001-wifi-to-ble-communication.md) | Accepted | `DL-001` |
| `ble-runtime-0002` | [Shared Transceiver firmware](ble-runtime-0002-shared-transceiver-firmware.md) | Superseded by `ble-runtime-0004` | `DL-004` |
| `ble-runtime-0003` | [Transceiver BLE PHY modes with Button switching](ble-runtime-0003-transceiver-phy-modes-button-switching.md) | Superseded by `ble-runtime-0004` (PHY content retained) | `DL-007` |
| `ble-runtime-0004` | [Single-image Transceiver with runtime roles](ble-runtime-0004-transceiver-runtime-roles-single-image.md) | Accepted — current architecture; LED behavior superseded by `ble-runtime-0005` | `DL-008` |
| `ble-runtime-0005` | [Transceiver role and radio activity indicators](ble-runtime-0005-transceiver-activity-indicators.md) | Superseded by `ble-runtime-0006` for TX indication; RX packet indication retained | — |
| `ble-runtime-0006` | [Shared TX state input and obstacle indication](ble-runtime-0006-shared-tx-state-and-obstacle-indication.md) | Accepted — current TX state input and indicator | — |
| `ble-runtime-0007` | [RX reception stub modes](ble-runtime-0007-rx-reception-stub-modes.md) | Accepted — RX test input and mode indication | — |
| `robot-runtime-0001` | [Dual-robot hardware binding](robot-runtime-0001-dual-robot-architecture.md) | Historical platform-selection record; current bindings updated by `robot-runtime-0003` | `DL-002` |
| `robot-runtime-0002` | [Current Dummy Robot hardware (Husky A200) and Radar acquisition](robot-runtime-0002-husky-radar-obstacle-footprint.md) | Accepted — hardware-specific | `DL-005` |
| `robot-runtime-0003` | [Robot-role abstraction and hardware binding](robot-runtime-0003-robot-role-abstraction-and-hardware-binding.md) | Accepted — current architecture rule | — |
| `robot-ros-0001` | [Controlled Robot control bridge (serial → local ROS)](robot-ros-0001-jackal-control-serial-ssh-ros.md) | Accepted — direct USB/local ROS current architecture; SSH archived as smoke-test transport | `DL-003` |
| `robot-hardware-0001` | [Husky power and troubleshooting conventions](robot-hardware-0001-husky-power-troubleshooting-conventions.md) | Accepted | `DL-006` |

## Experiment context

The baseline sensing system places the radar and RIS at the corner between two corridors/routes. One corridor is observed directly by the radar and the other through the RIS-assisted sensing path. The robotics contribution is intentionally kept simple: a mobile robot is teleoperated along one route, while the Radar/RIS system reports whether a moving person or obstacle is present in the conflicting route.

The current target end-to-end control story is:

```text
Radar/RIS object detection
        → serial trigger
        → NRF TX
        → BLE
        → NRF RX
        → USB serial directly into Controlled Robot onboard computer
        → persistent local serial / ROS bridge
        → Controlled Robot ROS safety input
        → command arbitration above joystick control
```

The 2026-10-05 external-laptop serial → SSH → ROS route remains preserved as successful smoke-test evidence, but SSH is no longer part of the target stopping path. The next robot-side validation is direct USB into the Controlled Robot onboard computer, followed by explicit STOP/release validation and end-to-end stopping-latency measurement.

The current DSP implementation now exposes the stabilized voted label and includes the obstacle-state/serial adapter in `dsp/integration/`. Experiment use is still blocked by placeholder inference, and the live DSP-to-TX hardware boundary remains to be validated. The BLE transport is implemented and hardware-smoke-tested.

The active architecture is dual-role: `DUMMY_ROBOT` / **Dummy Robot** occupies the conflicting corridor and `CONTROLLED_ROBOT` / **Controlled Robot** occupies the controlled corridor. Both current bindings are Clearpath Husky A200, referring to separate physical instances when both roles are present. The Controlled Robot remains under normal `cmd_vel` with a higher-priority local STOP authority. A Radar-side 2.0 m corner trigger is specified as design-only; its range calibration, release behavior, and stopping-distance validation remain open.

These records capture architecture choices around that integration while keeping the primary research contribution focused on Radar/RIS detection rather than autonomous navigation.
