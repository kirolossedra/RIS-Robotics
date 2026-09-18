# Decision Logs

This directory records significant design decisions for the RIS Robotics experiment.

| ID | Decision | Status |
|---|---|---|
| [DL-001](DL-001-communication-wifi-to-ble.md) | Use BLE instead of Wi-Fi for the Radar/RIS-to-robot safety signal | Accepted |
| [DL-002](DL-002-robot-platform-husky-to-jackal.md) | Dual-robot architecture: Husky = Dummy Robot; Jackal = Controlled Robot | Accepted — current architecture |
| [DL-003](DL-003-jackal-control-serial-ssh-ros.md) | Bridge safety state into Jackal control and enforce distance-gated STOP over `cmd_vel` | Accepted for initial implementation |
| [DL-004](DL-004-shared-transceiver-firmware.md) | Use one shared Transceiver firmware with TX/RX roles, coded S=8 advertising, and latched `OBS`/`CLR` state | Accepted |
| [DL-005](DL-005-husky-radar-obstacle-footprint.md) | Use Husky as the Dummy Robot and preserve sensing height while augmenting the target for detectability | Accepted |
| [DL-006](DL-006-husky-power-troubleshooting-conventions.md) | Standardize Husky computer power, bottom-up troubleshooting, incident separation, and preservation of original photo evidence | Accepted |

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

The sensing-team boundary is deliberately narrow: the team needs to expose the relevant object-detection event in its existing processing pipeline and allow that event to be emitted over serial. BLE transport, the robot-side bridge, and ROS stop arbitration are handled on the robotics side.

The active system is dual-robot: the Husky is the **Dummy Robot** moving in the conflicting corridor, while the Jackal is the **Controlled Robot** in the controlled corridor. Jackal motion still has two authorities—normal `cmd_vel` and higher-priority STOP—with distance-to-corner used only as gating context. `DISTANCE_THRESHOLD` and the distance source/method remain TBD.

These records capture architecture choices around that integration while keeping the primary research contribution focused on Radar/RIS detection rather than autonomous navigation.
