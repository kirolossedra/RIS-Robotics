# DL-005 — Husky Initial Role: Radar Obstacle-Footprint Data Collection

**Status:** Accepted  
**Date:** 2026-09-17  
**Scope:** Initial Husky use in the RIS Robotics experiment

## Decision

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

## Relationship to the Jackal decision

This decision does not reverse DL-002. The Jackal remains the selected platform for the later sensing-to-action demonstration and robot-control integration.

The Husky is being used first for a narrower purpose: providing a repeatable physical obstacle for Radar/RIS data collection before the project proceeds into robot-control troubleshooting.

## Consequence

The initial Husky work should focus only on obtaining useful Radar measurements of the obstacle footprint under stationary and moving-target conditions in the corridor. No Husky software or connection troubleshooting should be introduced until the dedicated Husky troubleshooting session begins.
