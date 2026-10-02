# Decision: Husky Dummy Robot and Radar Acquisition Configuration

**ID:** `robot-runtime-0002`
**Previous ID:** `DL-005`
**Status:** Accepted  
**Date:** 2026-09-17  
**Scope:** Current Dummy Robot hardware binding and robot-detectability configuration

## Decision

The current `DUMMY_ROBOT` hardware binding is the **Clearpath Husky A200**. In this experiment configuration it provides the repeatable moving physical obstacle in the conflicting / hidden corridor for Radar/RIS sensing and acquisition.

The 2026-09-17 acquisition session also established an experiment-configuration decision: the preferred sensing height was retained because lowering the sensing setup improved robot visibility but negatively affected human detection. Instead, bags were placed **on top of the Husky** as an experimental intervention intended to increase the target's effective physical height and improve its apparent radar visibility / apparent RCS. This does not claim a guaranteed or quantified electromagnetic RCS increase.

The first Husky activity will be limited to **Radar data collection for the obstacle footprint**.

During this phase, the Husky is not being treated as an actively controlled robotics platform. It is simply a physical obstacle placed in the corridor so that the Radar/RIS sensing setup can observe and characterize the obstacle footprint.

The Husky may be:

- stationary in the corridor; or
- moved through the corridor as a simple physical target.

For this initial phase, the Husky is intentionally a **dumb obstacle** from the experiment's point of view.

## What is explicitly out of scope for this phase

This phase does **not** require:

- ROS integration on the Husky;
- `cmd_vel` control;
- SSH control of the Husky;
- BLE-triggered stop behavior;
- autonomous navigation;
- localization, mapping, or path planning;
- robot-side safety-command arbitration.

Those robotics-control concerns belong to later troubleshooting and integration work and should not block the first Radar footprint measurements.

## Relationship to the Controlled Robot binding

`robot-runtime-0001` records the selected physical platforms, while `robot-runtime-0003` makes the roles architectural abstractions. The current bindings are:

- `DUMMY_ROBOT` → **Clearpath Husky A200** in the conflicting corridor.
- `CONTROLLED_ROBOT` → **Clearpath Jackal** in the controlled corridor.

The current Dummy Robot hardware does not participate in the Controlled Robot motion-control path.

## Consequence

The Husky work focuses on obtaining useful Radar/RIS measurements of the robot target under stationary and moving-target conditions in the corridor. For the acquisition geometry, preserving human detectability takes precedence over permanently lowering the sensing setup solely to improve robot visibility; target-side augmentation is the accepted experimental workaround from the 2026-09-17 session.

The robot-movement acquisition campaign performed on 2026-09-17 was concluded. This does not imply completion of the overall RIS Robotics project.
