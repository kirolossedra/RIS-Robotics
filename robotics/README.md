# Robotics

This directory is the working area for robot-side connectivity, control, and troubleshooting in the RIS Robotics system.

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

## Robot directories

### Husky

`husky/` records the Clearpath Husky A200 troubleshooting work used to prepare the robot for the initial Radar obstacle-footprint data-collection phase.

Current records:

- [TS-001 — Husky Onboard Computer Not Powering Up](husky/TS-001-onboard-computer-no-power-reversed-polarity.md) — initial Ethernet failure traced upstream to the onboard computer being unpowered; root cause was reversed polarity on the 12 V computer-power feed, resolved by correcting the polarity.

## Current focus

The immediate focus is establishing and verifying the robot connection path before integrating it with the wider RIS/Radar/BLE control flow.

For the initial Husky phase, the robot is being prepared only as a simple moving or stationary physical obstacle for Radar obstacle-footprint data collection. Higher-level Husky control integration is not assumed by that experimental role.

As troubleshooting progresses, add connection notes, diagnostic commands, logs, scripts, and confirmed procedures here rather than mixing robot-specific investigation into `firmware/` or `system/`.
