# Serial Integration

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Current documents](#current-documents)
- [Ownership boundaries](#ownership-boundaries)

## Purpose

This directory owns robot-side serial integration exploration and implementation evidence for the RIS Robotics control path.

The immediate concern is the serial boundary between the nRF52833 Transceiver firmware and the host computer that will forward `OBS` / `CLR` state toward the `CONTROLLED_ROBOT` ROS safety-stop interface.

## Scope

Use this directory for:

- host discovery of connected Transceiver serial interfaces;
- observed Linux and Windows serial-device behavior;
- validation of `OBS` / `CLR` delivery from the RX Transceiver to the host;
- analysis of the firmware serial implementation when it affects host integration;
- serial framing, liveness, reconnect, and state-synchronization exploration;
- evidence needed before the serial-to-SSH bridge is implemented;
- repeatable serial bring-up and validation procedures once the implementation stabilizes.

## Current documents

- [`exploration.md`](exploration.md) — 2026-10-05 exploration of the nRF52833 RX/TX LED states, RX stub behavior, Linux J-Link ACM interfaces, observed serial output, natural over-the-air reception, and the conclusion that the current `printk()` / `uart_poll_in()` console path is prototype-grade and should be replaced by a dedicated serial transport before the robot bridge is treated as production-ready.

## Ownership boundaries

The embedded Transceiver implementation remains owned by [`../../firmware/transceiver/`](../../firmware/transceiver/). This directory records robot-side serial integration evidence and conclusions rather than duplicating the firmware source of truth.

Transport-independent `OBS` / `CLR` semantics remain under [`../protocol-design/`](../protocol-design/). ROS-specific binding to the `CONTROLLED_ROBOT` safety-stop interface remains under [`../controller/ros/`](../controller/ros/).

The current integration boundary is:

```text
TX host / local TX input
        |
        v
nRF TX Transceiver
        |
       BLE
        |
        v
nRF RX Transceiver
        |
   serial OBS/CLR
        |
        v
Controlled Robot-side host
        |
 persistent SSH bridge
        |
        v
CONTROLLED_ROBOT ROS safety-stop interface
```

The serial link documented here owns only the Transceiver-to-host state-transfer boundary. It does not own ROS motion arbitration, which remains local to the `CONTROLLED_ROBOT`.
