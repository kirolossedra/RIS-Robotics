# Serial Integration

## Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Current documents](#current-documents)
- [Ownership boundaries](#ownership-boundaries)

## Purpose

This directory owns robot-side serial integration exploration and implementation evidence for the RIS Robotics control path.

The immediate concern is the serial boundary between the nRF52833 Transceiver firmware and the host computer that forwards `OBS` / `CLR` state toward the `CONTROLLED_ROBOT` ROS safety-stop interface.

## Scope

Use this directory for:

- host discovery of connected Transceiver serial interfaces;
- observed Linux and Windows serial-device behavior;
- validation of `OBS` / `CLR` delivery from the RX Transceiver to the host;
- analysis of the firmware serial implementation when it affects host integration;
- serial framing, liveness, reconnect, and state-synchronization exploration;
- serial-to-SSH bridge implementation history and operating procedures;
- repeatable serial bring-up and validation procedures once the implementation stabilizes.

## Current documents

- [`exploration.md`](exploration.md) — 2026-10-05 exploration of the nRF52833 RX/TX LED states, RX stub behavior, Linux J-Link ACM interfaces, observed serial output, natural over-the-air reception, and the conclusion that the original `printk()` / `uart_poll_in()` console path was prototype-grade and required a dedicated serial transport before robot integration.
- [`explanation.md`](explanation.md) — evolution from isolated serial validation through bridge v1-v8, the failures and corrections that produced the working v8 bridge, the final preemptive latest-state-wins design, exact operating procedure, troubleshooting evidence, and the remaining stop-latency concern.
- `serial-test-v2.py` — known-good isolated serial validation listener for exact newline-delimited `OBS` / `CLR` framing.
- `serial-ssh-bridge-v1.py` through `serial-ssh-bridge-v8.py` — preserved implementation evolution of the serial-to-SSH bridge. `serial-ssh-bridge-v8.py` is the current physically exercised version.

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
 specific SSH remote command
        |
        v
CONTROLLED_ROBOT ROS safety-stop interface
```

The serial integration documented here owns the Transceiver-to-host state-transfer boundary and the host-side forwarding bridge. It does not own ROS motion arbitration, which remains local to the `CONTROLLED_ROBOT`.
