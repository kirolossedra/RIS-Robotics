# System Interfaces

## Contents

- [Purpose](#purpose)
- [Interface maturity](#interface-maturity)
- [DSP classification to obstacle adapter](#dsp-classification-to-obstacle-adapter)
- [DSP to NRF TX serial](#dsp-to-nrf-tx-serial)
- [NRF TX to NRF RX BLE](#nrf-tx-to-nrf-rx-ble)
- [NRF RX to host serial](#nrf-rx-to-host-serial)
- [Host serial to Controlled Robot bridge](#host-serial-to-controlled-robot-bridge)
- [Bridge to Controlled Robot ROS](#bridge-to-controlled-robot-ros)
- [Distance-to-corner input](#distance-to-corner-input)
- [Compatibility rules](#compatibility-rules)

## Purpose

This document defines data contracts at subsystem boundaries. It distinguishes implemented protocols from planned interfaces so downstream work can integrate without reverse-engineering assumptions from prose.

## Interface maturity

| Boundary | Status |
|---|---|
| Voted label -> obstacle state | Implemented + software-tested |
| Obstacle state -> NRF TX UART | Implemented + software-tested; live-DSP hardware validation pending |
| NRF TX -> BLE -> NRF RX | Implemented + hardware smoke-tested |
| NRF RX -> Python JSONL logger | Implemented; hardware logger run pending |
| NRF RX -> Controlled Robot-side bridge | Design only |
| Bridge -> ROS safety input | Design only |
| Distance source -> ROS gate | TBD |

## DSP classification to obstacle adapter

Source: `dsp/collect_data_realtime.py` after the rolling vote.

| Stabilized label | Semantic state |
|---|---|
| `Person detected` | `OBSTACLE` |
| `Robot detected` | `OBSTACLE` |
| `Nothing detected` | `CLEAR` |
| unknown/invalid label | hold previous state + record fault |

The adapter initializes `CLEAR` to match the NRF TX boot state. It emits a semantic transition only when the state changes.

**Important:** with `PLACEHOLDER_MODE = True`, these labels are not experiment-valid detections. Normal startup therefore refuses serial control output unless the development-only override is explicitly used.

## DSP to NRF TX serial

Implementation: `dsp/integration/serial_output.py` -> NRF TX console.

- Transport: UART/USB serial.
- Default baud: **115200**, 8N1.
- Valid command lines: exact ASCII `OBS` or `CLR`, terminated by newline/CRLF.
- `OBS` means obstacle/unsafe state.
- `CLR` means clear state.
- Same-state repetitions are unnecessary; the DSP writer is transition-oriented and the TX firmware also latches state.
- Invalid lines are ignored by firmware.
- Serial device selection is automatic and only succeeds on an unambiguous candidate; failure/ambiguity disables serial rather than guessing.

## NRF TX to NRF RX BLE

Implementation: `firmware/transceiver/src/main.c` and `protocol.h`.

- BLE uses non-connectable extended advertising.
- Default PHY is LE Coded S=8; LE 1M is switchable at runtime.
- Service Data uses UUID `7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11`.
- Protocol version byte: `0x01`.
- State byte: `0x00 = CLR`, `0x01 = OBS`.
- RX validates type, length, UUID, and version before accepting the state.
- RX suppresses repeated advertisements of the same state.

## NRF RX to host serial

RX serial output is transition-oriented:

```text
air:    OBS OBS OBS CLR CLR OBS
serial: OBS         CLR     OBS
```

An initial `CLR` is silent. `CLR` is emitted only after RX has emitted an `OBS` in the current observation epoch. A PHY switch starts a fresh RX observation epoch.

`firmware/tools/rx_logger.py` can timestamp accepted serial transitions in UTC JSON Lines. The logger implementation exists; a dedicated hardware JSONL validation run remains open.

## Host serial to Controlled Robot bridge

**Status: design only. No bridge implementation exists in the repository.**

The accepted architecture requires a Controlled Robot-side process to consume the RX transition stream and maintain a persistent SSH connection to the Controlled Robot onboard computer. Exact process API, reconnect behavior, state resynchronization, and stale-event policy are still implementation work.

## Bridge to Controlled Robot ROS

**Status: design only.**

The bridge may trigger a ROS-side safety input over the already-open SSH session, but the final STOP precedence must be enforced locally on the Controlled Robot. No repository code currently defines the ROS topic/action, launch configuration, mux/supervisor, or command-arbitration node.

## Distance-to-corner input

**Status: TBD.**

No source, estimator, sensor, localization mechanism, update rate, units contract, threshold calibration procedure, or stale-data policy has been selected. The only accepted semantic requirement is that distance is contextual gating state for STOP enforcement; it is not a third motion authority.

## Compatibility rules

- Do not change `OBS`/`CLR`, packet UUID, version, or state-byte meaning without a coordinated interface decision and updates on both firmware roles.
- Do not infer `CLR` from transport silence.
- Do not enable the DSP serial output for experiment use while placeholder inference is active.
- Do not specify a ROS interface in system docs before the actual Controlled Robot implementation selects it.
