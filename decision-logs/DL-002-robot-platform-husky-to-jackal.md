# DL-002 — Robot Roles: Dual-Robot Architecture

**Status:** Accepted — current architecture  
**Date:** 2026-09-17  
**Scope:** Robot roles in the RIS Robotics experiment

## Current decision

The experiment retains **both** Clearpath robots with distinct roles.

- **Husky = Dummy Robot.** The Husky operates in the conflicting / hidden corridor as the moving physical obstacle observed by the Radar/RIS system. It exists to provide repeatable robot movement for sensing; sophisticated Husky autonomy is irrelevant.
- **Jackal = Controlled Robot.** The Jackal operates in the controlled corridor. It remains manually teleoperated through `cmd_vel` and is the robot subject to the Radar/RIS-derived safety-control logic.

This supersedes the earlier interpretation that Jackal simply replaced Husky as the experiment robot. Jackal remains the simpler controlled platform for the sensing-to-action demonstration, while Husky has gained a separate, non-control role as the moving Dummy Robot.

## Two-corridor model

```text
Husky / Dummy Robot
        |
        | movement
        v
Conflicting / hidden corridor
        |
        v
Radar / RIS sensing
        |
        v
obstacle / occupancy state

Teleoperator
        |
        | cmd_vel
        v
Jackal / Controlled Robot
        |
        v
Controlled corridor
```

The Husky is not part of the Jackal control path. The Radar/RIS system does not directly command Jackal motors; it derives compact safety state. The Jackal-side computer owns the final control arbitration.

## Consequences

The historical Jackal-selection reasoning remains useful: both platforms can support teleoperation plus a safety override, and Jackal keeps the controlled-robot side operationally simple. That reasoning now applies specifically to **which robot is controlled**, not to eliminating Husky from the experiment.

The current progression is:

```text
Initial Husky concept
    ->
Jackal selected as controlled experiment robot
    ->
Dual-robot architecture
    Husky = Dummy Robot
    Jackal = Controlled Robot
```

---

## Archived Decisions

> **ARCHIVED — historical engineering decision**
>
> **Introduced:** 2026-09-15  
> **Superseded:** 2026-09-17  
> **Superseded by:** Dual-robot architecture — Husky = Dummy Robot; Jackal = Controlled Robot  
> **Reason:** Jackal remains the controlled robot, while Husky gained a distinct role as the moving Dummy Robot in the conflicting corridor. The earlier platform-selection reasoning remains valid for the controlled-robot role, but the conclusion that Jackal replaces Husky in the overall experiment no longer represents the active architecture.

### Previous Decision: Husky -> Jackal

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

There was also a practical reason the Husky was initially convenient: it had previously been easy to borrow because it was already being used as part of the Rogers project. That existing project access reduced the administrative overhead of getting the platform for testing.

## Revised decision — Clearpath Jackal

The experiment will instead use a Clearpath Jackal.

The reason for the change is practical simplicity. The Jackal is easier to use for this corridor/corner experiment and reduces the physical and operational overhead of the robotics portion of the test. The experiment does not benefit from making the mobile platform itself more complex than necessary.

The architecture remains the same:

- the Jackal is teleoperated normally;
- the Radar/RIS system derives the conflicting-corridor hazard state;
- the hazard state is transmitted using BLE through NRF boards;
- the Jackal computer receives that state;
- a local safety supervisor has higher priority than the normal velocity command and prevents the robot from proceeding when the conflicting corridor is occupied.

## Husky vs Jackal tradeoffs

This comparison is intentionally written for the full project team, including members who are not robotics specialists. Both platforms are technically capable of supporting the required experiment; the distinction is mainly in operational simplicity, access, and setup overhead.

| Tradeoff | Husky | Jackal | Impact on this experiment |
|---|---|---|---|
| **Technical suitability** | Suitable for teleoperation + safety-stop override | Suitable for teleoperation + safety-stop override | **No meaningful difference for the core experiment.** Neither needs autonomous navigation, SLAM, or localization. |
| **Previous familiarity** | Already used extensively in the Rogers project | New platform for this specific work | Husky has lower familiarity/setup risk initially. |
| **Previous access** | Was easy to borrow while working on the Rogers project | Available, but taking it to the office requires additional administrative steps | Husky historically had easier access under the previous project context. |
| **Current operating access** | Previous convenient arrangement no longer applies in the same way | Practical to use during normal working hours | Current plan favors using Jackal during typical working hours rather than moving it to the office. |
| **After-hours / office use** | Previously easier to arrange | Requires extra red tape and a professor's signature to move it to the office | Jackal introduces an operational constraint if experiments need to happen outside its normal location/hours. |
| **Physical deployment** | Larger/more operational overhead for the simple corridor experiment | Easier and simpler to deploy for this experiment | **Jackal advantage.** The robot is only an actuator for demonstrating the Radar/RIS safety response. |
| **Experiment complexity** | More robot than the experiment requires | Better aligned with the intentionally simple robotics role | Jackal helps keep engineering effort focused on Radar/RIS detection, BLE communication, and the safety interlock. |
| **Data-collection laptop mounting** | No specific convenient mounting arrangement identified in the current plan | Currently has a **wooden rack/platform** suitable for the data-collection laptop | **Jackal advantage.** Less mechanical/setup work before testing. |
| **Robot-side architecture** | `cmd_vel` + higher-priority safety override | `cmd_vel` + higher-priority safety override | Same architecture. Changing robots does **not** change the experimental concept. |
| **Main downside of switching** | Already familiar and previously convenient to access | Some additional learning/setup plus stricter access logistics | The Jackal choice is operationally simpler during experiments, but administratively less flexible if we want to relocate it. |
| **Main reason for selection** | Technically capable, but offers no necessary advantage for this test | Simpler physical platform for the required demonstration | **Jackal selected because it achieves the required function with less unnecessary robotics complexity.** |

The key interpretation is simple: both robots can perform the required task. Jackal is not being selected because it provides better sensing or more advanced autonomy. It is being selected because it is simpler to operate for this experiment and already provides a practical mounting arrangement for the data-collection laptop. The tradeoff is reduced flexibility when moving the platform outside its normal working arrangement.

## Operational access constraint

Unlike the previous Husky arrangement, taking the Jackal away from its normal working area and into the office requires additional administrative approval, including extra paperwork and a professor's signature.

To avoid making the robotics portion of the experiment dependent on that additional borrowing process, the current operating plan is to use the Jackal during normal working hours in its usual accessible environment rather than routinely moving it to the office.

This is an operational constraint rather than a technical limitation of the Jackal. It affects when and where experiments are scheduled, but it does not change the sensing-to-stop architecture.

## Physical setup advantage

The Jackal currently has a wooden rack/platform mounted on it. The data-collection laptop can be placed on this rack during experiments.

This is useful for the planned setup because the laptop can remain physically on the robot while it:

- receives or logs the BLE safety state from the NRF board connected to the Jackal-side computer;
- records experiment data;
- supports the local safety-supervisor process and any required robot-side monitoring.

The rack therefore reduces the need to design an additional laptop-mounting solution for the first implementation.

## Why the decision changed

Moving from Husky to Jackal keeps the implementation aligned with the actual research objective:

- easier physical deployment and operation for the corridor test;
- less robot-platform overhead for a test that does not require autonomous navigation;
- simpler experimental handling while preserving the required motion-control interface;
- an existing wooden rack that can carry the data-collection laptop;
- keeps engineering effort focused on Radar/RIS detection, BLE communication, and the stop-interlock behavior.

The tradeoff is that Jackal access is administratively less flexible than the Husky access previously available through the Rogers project. Because office borrowing requires additional approval and a professor's signature, testing will be planned primarily during normal working hours.

The goal is not to optimize or benchmark the robot platform. The robot should be the simplest competent platform for demonstrating the sensing-to-action chain.

## Consequences

Any robot-side implementation, launch configuration, topic/interface names, and hardware connections must target the Jackal rather than the Husky.

The safety behavior remains unchanged: a hazard indication must be able to override normal commanded motion locally on the robot computer.

Experiment scheduling should assume Jackal use during normal working hours unless the additional approval process for moving the platform is completed.

The existing wooden rack should be treated as the default mounting location for the data-collection laptop unless a later experiment requires a different mechanical arrangement.

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
