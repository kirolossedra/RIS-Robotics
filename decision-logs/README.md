# Decision Logs

This directory records significant design decisions for the RIS Robotics experiment.

| ID | Decision | Status |
|---|---|---|
| [DL-001](DL-001-communication-wifi-to-ble.md) | Use BLE instead of Wi-Fi for the Radar/RIS-to-robot safety signal | Accepted |
| [DL-002](DL-002-robot-platform-husky-to-jackal.md) | Use Clearpath Jackal instead of Husky for the mobile robot | Accepted |

## Experiment context

The baseline sensing system places the radar and RIS at the corner between two corridors/routes. One corridor is observed directly by the radar and the other through the RIS-assisted sensing path. The robotics contribution is intentionally kept simple: a mobile robot is teleoperated along one route, while the Radar/RIS system reports whether a moving person or obstacle is present in the conflicting route. When the conflicting route is occupied, a robot-side safety supervisor must prevent the robot from proceeding into the unsafe section.

These records capture architecture choices around that integration while keeping the primary research contribution focused on Radar/RIS detection rather than autonomous navigation.
