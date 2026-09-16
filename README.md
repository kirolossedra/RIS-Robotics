# RIS-Robotics

Integration project connecting the existing Radar/RIS sensing pipeline to a Clearpath Jackal so that a detected conflicting condition can assert a higher-authority STOP over normal joystick motion.

## Current architecture

The project is intentionally narrow: the sensing system produces an object-detection event, that event is converted to a serial trigger, transported over BLE using two NRF boards, received on the Jackal-side laptop, forwarded through a persistent SSH session over Ethernet to the Jackal's onboard ROS computer, and enforced locally through ROS command arbitration.

```text
Radar/RIS detection
  → serial
  → NRF TX
  → BLE
  → NRF RX
  → serial
  → Jackal-side laptop
  → persistent SSH / Ethernet
  → Jackal ROS safety input
  → STOP-over-joystick arbitration
```

## Documentation

- [`system/system.md`](system/system.md) — full-system architecture, responsibility boundaries, current assumptions, status, and bigger picture.
- [`system/control-signal-path.md`](system/control-signal-path.md) — detailed control-signal journey, exact sensing-team ask, robotics-side deliverables, dependencies, and integration plan.
- [`decision-logs/`](decision-logs/) — design decisions, including BLE transport, Jackal platform selection, and the serial-to-SSH-to-ROS control bridge.

The software STOP path is part of the research integration and does not replace the Jackal's physical emergency stop or normal supervised laboratory safety procedures.