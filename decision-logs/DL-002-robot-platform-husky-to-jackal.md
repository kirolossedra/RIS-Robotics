# DL-002 — Robot Platform: Husky to Jackal

**Status:** Accepted  
**Date:** 2026-09-15  
**Scope:** Mobile robot used in the RIS Robotics experiment

## Context

The robotics portion of the experiment is intentionally limited. The robot does not need to perform autonomous localization, mapping, or path planning. It only needs to be teleoperated along the test route and obey a higher-priority stop decision when the Radar/RIS system reports a moving person or obstacle in the conflicting corridor.

The primary research contribution remains the Radar/RIS sensing and detection behavior. The robot is the physical actuator used to demonstrate that the sensing result can influence motion safely at the corner.

## Initial decision — Clearpath Husky

The first plan used a Clearpath Husky. The expected robot-side integration was straightforward: normal teleoperation would produce velocity commands, while a safety supervisor would be inserted with higher priority so that a received hazard state could force the output velocity to zero.

Conceptually:

```text
Teleoperation command ----\
                           > Safety supervisor --> Robot controller
BLE hazard state --------/
```

The Husky was therefore technically suitable for the experiment.

## Revised decision — Clearpath Jackal

The experiment will instead use a Clearpath Jackal.

The reason for the change is practical simplicity. The Jackal is easier to use for this corridor/corner experiment and reduces the physical and operational overhead of the robotics portion of the test. The experiment does not benefit from making the mobile platform itself more complex than necessary.

The architecture remains the same:

- the Jackal is teleoperated normally;
- the Radar/RIS system derives the conflicting-corridor hazard state;
- the hazard state is transmitted using BLE through NRF boards;
- the Jackal computer receives that state;
- a local safety supervisor has higher priority than the normal velocity command and prevents the robot from proceeding when the conflicting corridor is occupied.

## Why the decision changed

Moving from Husky to Jackal keeps the implementation aligned with the actual research objective:

- easier physical deployment and operation for the corridor test;
- less robot-platform overhead for a test that does not require autonomous navigation;
- simpler experimental handling while preserving the required motion-control interface;
- keeps engineering effort focused on Radar/RIS detection, BLE communication, and the stop-interlock behavior.

The goal is not to optimize or benchmark the robot platform. The robot should be the simplest competent platform for demonstrating the sensing-to-action chain.

## Consequences

Any robot-side implementation, launch configuration, topic/interface names, and hardware connections must target the Jackal rather than the Husky.

The safety behavior remains unchanged: a hazard indication must be able to override normal commanded motion locally on the robot computer.

As with the previous platform choice, the software stop is part of the research integration and does not replace the Jackal's physical emergency-stop mechanism or supervised test procedures when people are present.

## Resulting experimental chain

```text
Radar / RIS detects moving obstacle
              |
              v
       Safety state generated
              |
              v
      NRF -- BLE --> NRF
                      |
                      v
               Jackal computer
                      |
              Safety supervisor
                      |
          allow cmd_vel / force stop
                      |
                      v
                    Jackal
```
