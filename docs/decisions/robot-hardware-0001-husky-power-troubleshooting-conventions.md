# Decision: Husky Power and Troubleshooting Conventions

**ID:** `robot-hardware-0001`
**Previous ID:** `DL-006`
**Status:** Accepted  
**Date:** 2026-09-17  
**Scope:** Husky hardware troubleshooting and documentation

## Decision

The Husky onboard computer will use the robot's **12 V / 5 A user-power rail** as its computer power source. The 24 V rail is not part of the onboard-computer power path.

The working polarity/orientation established during TS-001 is now the **canonical computer-power configuration** for this Husky. A physically seated connector is not sufficient evidence that the power path is correct; the known-good polarity/orientation must be preserved.

The two loose barrel-style outputs on the existing split 12 V harness are **not required for the onboard computer** and will remain unused unless a future accessory is deliberately assigned to them.

Future Husky troubleshooting will proceed bottom-up in the following order:

```text
1. Husky base power
2. Onboard-computer power
3. Ethernet physical link
4. IP configuration / reachability
5. SSH / operating-system access
6. ROS and robot interfaces
7. Controller pairing / teleoperation
```

A resolved root cause will close its troubleshooting record. A subsequent, independent failure becomes a new incident rather than extending the old record indefinitely. For example, the reversed-polarity computer-power fault is TS-001; any remaining Ethernet or controller issue is a separate troubleshooting incident.

For Husky hardware troubleshooting, the repository will preserve the **actual photos captured during the session**. Images should be stored alongside the incident documentation, referenced with repository-relative Markdown paths, and rendered inline in the corresponding troubleshooting Markdown. Generated, resized, or recompressed substitutes should not replace the original evidence unless explicitly created as a separate annotated derivative.

### Canonical robot-side working directory and log placement

On **Husky 1**, the canonical project working directory is:

```text
/home/robot/robohub/WSDL/kiro
```

When commands, scripts, captures, or troubleshooting artifacts are created on the robot for this project, this directory is the source-of-truth working location unless an existing project path explicitly requires a more specific subdirectory.

Bluetooth joystick logs must be stored under:

```text
/home/robot/robohub/WSDL/kiro/logs/BLE/joystick/
```

Do not save project troubleshooting logs to arbitrary locations such as the user's home directory when the canonical project tree is available.

For future joystick/Bluetooth investigations, commands that persist scan output, diagnostics, or other evidence should write into `logs/BLE/joystick/`.

## Rationale

The first Husky troubleshooting session began as an apparent Ethernet problem, but the actual failure was below the network layer: the onboard computer was not receiving usable power because the 12 V polarity was reversed. The computer power connector was physically present, so visual inspection of connector seating alone did not reveal the fault.

This established two important practices. First, the known-good 12 V wiring state should be treated as configuration, not rediscovered each time. Second, future debugging should move from physical power upward through networking and software so that higher-level symptoms do not hide lower-level failures.

Preserving the original photos with each incident keeps the physical wiring evidence tied to the conclusions drawn from it and makes later reconstruction of the robot state possible.

Using one canonical project directory on the robot prevents evidence from being scattered across arbitrary shell locations. Keeping Bluetooth joystick evidence under `logs/BLE/joystick/` makes recurring controller failures directly comparable across sessions and preserves the operational history beside the project itself.

## Related records

- `robotics/husky/TS-001-onboard-computer-no-power-reversed-polarity.md` — reversed-polarity incident and resolution.
- `robotics/husky/TS-002-ps4-controller-bluetooth-pairing.md` — PS4 / DualShock 4 Bluetooth pairing investigation and recovery.
- `robot-runtime-0002-husky-radar-obstacle-footprint.md` — Husky's initial experimental role as a simple physical Radar obstacle/target for data collection.
