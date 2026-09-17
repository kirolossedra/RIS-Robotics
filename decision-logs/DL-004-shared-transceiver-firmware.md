# DL-004 — Shared NRF Transceiver Firmware

**Status:** Accepted  
**Date:** 2026-09-16  
**Scope:** Firmware organization, roles, radio PHY, and state protocol for the two NRF boards

## Decision

The NRF subsystem is named the **Transceiver**. TX and RX are build-time roles of one Zephyr application and share one source tree; they are not separate firmware projects.

- **TX role:** uses the board's `led0` and `led1` definitions, blinking both to identify the image. It accepts newline-delimited `OBS` and `CLR` over the board console and continuously advertises the current state.
- **RX role:** uses the board's `led0` definition, blinking it to identify the image. It scans for Transceiver advertisements and writes only logical state transitions as newline-delimited `OBS` and `CLR` serial events.

The state machine is latched: `OBS` remains active until `CLR`; `CLR` remains active until the next `OBS`. Repeated advertisements preserve radio reliability but RX suppresses duplicate logical events. RX also suppresses a startup `CLR`, because the required event pair begins with the first received `OBS` and ends with the first following `CLR`.

## BLE PHY

The link uses non-connectable extended advertising and passive scanning on LE Coded PHY only. With nRF Connect SDK v3.2.3, TX enables `CONFIG_BT_EXT_ADV_CODING_SELECTION` and requests `BT_LE_ADV_OPT_REQUIRE_S8_CODING` together with `BT_LE_ADV_OPT_CODED`. This is the SDK's explicit advertising coding-selection API and maps to the HCI extended-advertising-parameters-v2 S=8 requirement. RX enables coded-only scanning; the coding selection is made by the advertiser and reported by the controller.

This choice favors range over throughput. It also means this firmware requires a controller/board combination that supports extended advertising, LE Coded PHY, and advertising coding selection.

## Protocol and boundary

The serial protocol is ASCII, one command/event per line:

```text
OBS\n
CLR\n
```

BLE carries protocol version 1 and the current state in 128-bit Service Data identified by UUID `7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11`. The TX begins in `CLEAR` and repeatedly broadcasts its current state.

The implemented boundary ends at the RX-side Python logger. Persistent SSH, ROS arbitration, and `cmd_vel` control remain downstream work and are not implemented by the Transceiver.

## Consequences

- One codebase prevents TX/RX protocol drift.
- Role-specific Kconfig fragments produce separate images from the same sources.
- Board LED aliases are used instead of fixed GPIO pin numbers.
- Duplicate BLE packets do not create duplicate host events.
- A future safety decision is still required for stale or missing wireless data; radio silence is not emitted as `CLR`.

