# Decision Logs

This directory records significant design decisions for the RIS Robotics experiment.

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
| `ble-runtime-0004` | [Single-image Transceiver with runtime roles](ble-runtime-0004-transceiver-runtime-roles-single-image.md) | Accepted — current architecture | `DL-008` |
| `robot-runtime-0001` | [Dual-robot architecture](robot-runtime-0001-dual-robot-architecture.md) | Accepted — current architecture | `DL-002` |
| `robot-runtime-0002` | [Husky Dummy Robot and Radar acquisition](robot-runtime-0002-husky-radar-obstacle-footprint.md) | Accepted | `DL-005` |
| `robot-ros-0001` | [Jackal control bridge (serial → SSH → ROS)](robot-ros-0001-jackal-control-serial-ssh-ros.md) | Accepted for the initial implementation | `DL-003` |
| `robot-hardware-0001` | [Husky power and troubleshooting conventions](robot-hardware-0001-husky-power-troubleshooting-conventions.md) | Accepted | `DL-006` |

## Experiment context

The baseline sensing system places the radar and RIS at the corner between two corridors/routes. One corridor is observed directly by the radar and the other through the RIS-assisted sensing path. The robotics contribution is intentionally kept simple: a mobile robot is teleoperated along one route, while the Radar/RIS system reports whether a moving person or obstacle is present in the conflicting route.

The current end-to-end control story is:

```text
Radar/RIS object detection
        → serial trigger
        → NRF TX
        → BLE
        → NRF RX
        → serial
        → Jackal-side laptop
        → persistent SSH over Ethernet
        → Jackal ROS safety input
        → command arbitration above joystick control
```

The current DSP implementation now exposes the stabilized voted label and includes the obstacle-state/serial adapter in `dsp/integration/`. Experiment use is still blocked by placeholder inference, and the live DSP-to-TX hardware boundary remains to be validated. The BLE transport is implemented and hardware-smoke-tested; the robot-side bridge and ROS stop arbitration remain downstream design work.

The active system is dual-robot: the Husky is the **Dummy Robot** moving in the conflicting corridor, while the Jackal is the **Controlled Robot** in the controlled corridor. Jackal motion still has two authorities—normal `cmd_vel` and higher-priority STOP—with distance-to-corner used only as gating context. `DISTANCE_THRESHOLD` and the distance source/method remain TBD.

These records capture architecture choices around that integration while keeping the primary research contribution focused on Radar/RIS detection rather than autonomous navigation.
