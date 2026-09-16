# Decision Logs

This directory records significant design decisions for the RIS Robotics experiment.

| ID | Decision | Status |
|---|---|---|
| [DL-001](DL-001-communication-wifi-to-ble.md) | Use BLE instead of Wi-Fi for the Radar/RIS-to-robot safety signal | Accepted |
| [DL-002](DL-002-robot-platform-husky-to-jackal.md) | Use Clearpath Jackal instead of Husky for the mobile robot | Accepted |
| [DL-003](DL-003-jackal-control-serial-ssh-ros.md) | Bridge the received serial STOP state into the Jackal through persistent SSH, with ROS-side command arbitration | Accepted for initial implementation |

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

These records capture architecture choices around that integration while keeping the primary research contribution focused on Radar/RIS detection rather than autonomous navigation.