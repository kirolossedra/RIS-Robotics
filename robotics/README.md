# Robotics

This directory is the working area for robot-side connectivity, control, and troubleshooting in the RIS Robotics system.

## Scope

Use this directory to document and debug the path from the robot-side laptop to the Jackal, including:

- Ethernet connectivity between the laptop and Jackal
- SSH access and remote command execution
- ROS environment and topic visibility
- Publishing robot control commands such as `cmd_vel`
- Network/interface configuration and reachability
- Connection failures, observations, commands, and fixes discovered during troubleshooting

## Current focus

The immediate focus is establishing and verifying the robot connection path before integrating it with the wider RIS/Radar/BLE control flow.

As troubleshooting progresses, add connection notes, diagnostic commands, logs, scripts, and confirmed procedures here rather than mixing robot-specific investigation into `firmware/` or `system/`.
