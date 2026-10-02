# MUSE Session Log — 2026-10-02

## Table of contents

- [Husky 1 bring-up and Joystick 3 Bluetooth recurrence](#husky-1-bring-up-and-joystick-3-bluetooth-recurrence)

## Husky 1 bring-up and Joystick 3 Bluetooth recurrence

### Context

During work with **Husky 1** and **Joystick 3** on 2026-10-02, the robot was brought up again for manual-control preparation.

### Confirmed observations

- Husky 1 power was connected.
- Laptop-to-Husky communication worked.
- SSH access to the robot worked.
- The mounting plate had been mounted back onto the Husky.
- The PS4 / DualShock 4 controller issue recurred for **Joystick 3**.
- Joystick 3 is the controller previously recorded as **Husky 3**, Bluetooth MAC `48:18:8D:52:67:63`.
- Current working suspicion: the stored Bluetooth pairing/bond may no longer exist on Husky 1; this has not yet been confirmed from BlueZ state.
- The Husky Bluetooth adapter was verified with `hciconfig` as `hci0`, address `CC:D9:AC:3C:9E:24`, state `UP RUNNING PSCAN`.
- A fresh `sudo ds4drv-pair` attempt while Joystick 3 was in pairing mode returned `No Controller Found`.
- Canonical robot-side project path was clarified as `/home/robot/robohub/WSDL/kiro`.
- BLE joystick diagnostic logs must be stored under `/home/robot/robohub/WSDL/kiro/logs/BLE/joystick/`; arbitrary locations such as `~/` are not to be used for project evidence.

### Investigation boundary

Do not remove or recreate Bluetooth state until the robot's current state is inspected.

First check:

```bash
bluetoothctl devices | grep -Ei 'Wireless|Controller|Sony'
bluetoothctl info 48:18:8D:52:67:63
```

Interpretation:

- If `48:18:8D:52:67:63` is absent / `info` reports the device is unavailable, treat this as a missing stored bond and perform a fresh pairing.
- If it is present but reports paired/bonded/trusted and cannot connect, follow the established TS-002 stale-bond recovery: remove the device, put the controller into PS + SHARE pairing mode, then run `sudo ds4drv-pair`.
- Controller input and ROS teleoperation must be verified after Bluetooth recovery; successful pairing alone is not equivalent to successful robot control.

### Evidence-location correction

A prior proposed scan command targeted the user's home directory. That path is not the project source of truth and is superseded for this project.

All subsequent Bluetooth joystick scan evidence for this incident is to be written under:

```text
/home/robot/robohub/WSDL/kiro/logs/BLE/joystick/
```
