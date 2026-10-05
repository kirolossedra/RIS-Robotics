# Robotics

This directory is the working area for robot-side connectivity, control, and troubleshooting in the RIS Robotics system.

## Contents

- [Documentation authority](#documentation-authority)
- [Scope](#scope)
- [Robotics areas](#robotics-areas)
- [Current focus](#current-focus)

## Documentation authority

This directory owns robot-specific connectivity, hardware troubleshooting, images, and implementation evidence. Stable robot architecture uses `DUMMY_ROBOT` and `CONTROLLED_ROBOT` under [`../docs/architecture/`](../docs/architecture/); product names remain correct here because these records concern physical hardware.

The canonical troubleshooting index is [`../docs/troubleshooting/README.md`](../docs/troubleshooting/README.md).

## Scope

Use this directory to document and debug robot-side hardware and connectivity, including:

- robot power and onboard-computer startup
- Ethernet connectivity between an external laptop and the robot
- SSH access and remote command execution
- ROS environment and topic visibility
- publishing robot control commands such as `cmd_vel`
- network/interface configuration and reachability
- controller pairing and teleoperation
- connection failures, observations, commands, root causes, and confirmed fixes discovered during troubleshooting

## Robotics areas

- [Protocol design](protocol-design/README.md) — transport-independent message contracts and behavior algorithms, including Radar `OBS` overriding joystick control and the Radar-side Controlled Robot corner-proximity trigger.
- [Controller and integration](controller/README.md) — controller configuration and the ROS/runtime binding of protocol behavior.

### Husky

`husky/` records the Clearpath Husky A200 troubleshooting work used to prepare the robot for the initial Radar obstacle-footprint data-collection phase.

Current records:

- [TS-001 — Husky Onboard Computer Not Powering Up](husky/TS-001-onboard-computer-no-power-reversed-polarity.md) — initial Ethernet failure traced upstream to the onboard computer being unpowered; root cause was reversed polarity on the 12 V computer-power feed, resolved by correcting the polarity.
- [TS-002 — Husky PS4 Controller Bluetooth Pairing](husky/TS-002-ps4-controller-bluetooth-pairing.md) — full PS4/DualShock 4 pairing investigation for **Husky 3 / Joystick 3** (`48:18:8D:52:67:63`). The valid-looking `Paired/Bonded/Trusted` state followed by `br-connection-create-socket` was observed on 2026-09-17 and reproduced on 2026-10-02. Both incidents recovered after resetting the unusable stored record and cleanly re-pairing. The 2026-10-02 session also established timestamped BLE joystick logging under the canonical Husky project tree.
- [TS-003 — Husky Troubleshooting Images Not Rendering](husky/TS-003-husky-troubleshooting-images-not-rendering.md) — open report that images in the Husky troubleshooting docs are not loading properly; the referenced TS-001 image assets are present and the rendering cause remains unknown.

## Current focus

The immediate focus is establishing and verifying the robot connection path before integrating it with the wider RIS/Radar/BLE control flow.

For the initial Husky phase, the robot is being prepared only as a simple moving or stationary physical obstacle for Radar obstacle-footprint data collection. Higher-level Husky control integration is not assumed by that experimental role.

As troubleshooting progresses, add connection notes, diagnostic commands, logs, scripts, and confirmed procedures here rather than mixing robot-specific investigation into `firmware/` or `docs/architecture/`.
