# RIS-Robotics

Integration project connecting the existing Radar/RIS sensing pipeline to a dual-robot corridor experiment: a Clearpath Husky acts as the **Dummy Robot** in the conflicting corridor, while a Clearpath Jackal is the **Controlled Robot** in the controlled corridor.

## Current architecture

The system now has two distinct robot roles. The **Husky = Dummy Robot**: it moves in the conflicting / hidden corridor as the physical obstacle observed by Radar/RIS. The **Jackal = Controlled Robot**: it remains manually teleoperated in the controlled corridor through `cmd_vel` and is subject to the higher-priority experimental safety STOP.

The communication chain remains intentionally compact:

```text
Husky / Dummy Robot in conflicting corridor
  → Radar/RIS sensing
  → Central Laptop derives obstacle/safety state
  → USB → NRF TX → BLE Coded PHY S=8 → NRF RX → USB
  → Jackal-side computer
  → Ethernet / ROS control interface
  → safety gating + command arbitration
  → Jackal / Controlled Robot
```

STOP is enforced only when the conflicting corridor is unsafe **and** the Jackal is sufficiently close to the corner. Distance-to-corner is contextual gating state, not a third motion-control authority. `DISTANCE_THRESHOLD` and the distance-to-corner source/method remain **TBD**.

## Documentation

- [`system/system.md`](system/system.md) — full-system architecture, responsibility boundaries, current assumptions, status, and bigger picture.
- [`system/control-signal-path.md`](system/control-signal-path.md) — detailed control-signal journey, exact sensing-team ask, robotics-side deliverables, dependencies, and integration plan.
- [`decision-logs/`](decision-logs/) — design decisions, including BLE transport, Jackal platform selection, and the serial-to-SSH-to-ROS control bridge.
- [`firmware/`](firmware/) — shared TX/RX Transceiver firmware, RX serial logger, build, flashing, and smoke-test instructions.
- [`session-logs/2026-09-17.md`](session-logs/2026-09-17.md) — chronological record of the 2026-09-17 engineering session.

The software STOP path is part of the research integration and does not replace the Jackal's physical emergency stop or normal supervised laboratory safety procedures.

## Informal working TODO

This is intentionally a lightweight day-to-day list rather than a formal project plan. Detailed architecture and decisions remain in the documents above.

### Today — Wednesday, 2026-09-16

- [x] Implement the standalone shared **Transceiver TX → BLE → Transceiver RX** firmware path for the two available NRF boards.
- [x] Make the BLE path carry the latched `OBS` / `CLR` state using coded S=8 advertising.
- [ ] Hardware-smoke-test the robot-side Transceiver RX serial output on the two physical boards.
- [ ] If time permits, prepare the small laptop-side serial listener / persistent-SSH bridge so the received serial event can later cause a command to execute on the Jackal onboard computer.
- [ ] Keep the sensing-team questions and answer placeholders in [`system/control-signal-path.md`](system/control-signal-path.md) ready to fill in during the team session.

### Tomorrow — Thursday, 2026-09-17

**With the Radar/RIS team:**

- [ ] Confirm whether the object-detection result is accessible in the existing Radar/RIS processing pipeline as currently assumed.
- [ ] Identify the **exact pipeline block/module** where the relevant detection event becomes available.
- [ ] Record what that event/state actually looks like and how it can be accessed.
- [ ] Confirm where a **serial-output step** can be inserted and whether there are any serial/interface constraints we need to respect.
- [ ] Fill their answers directly into the dedicated response placeholders in the control-signal integration document.
- [ ] If the insertion point is immediately usable, connect the real detection event to the serial trigger feeding the NRF TX board and exercise as much of the sensing-to-BLE path as practical during the session.

**On the robotics side:**

- [ ] Continue the independent Jackal integration: **NRF RX → laptop serial → persistent SSH over Ethernet → Jackal onboard ROS**.
- [ ] Begin or continue the ROS-side STOP arbitration so the Radar/RIS-derived STOP can override normal joystick velocity commands.
- [ ] Keep the final end-to-end integration as the last step once the sensing-side trigger and robot-side STOP path are both ready independently.
