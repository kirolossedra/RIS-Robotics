# Configuration and Operations

## Contents

- [Purpose](#purpose)
- [Supported hardware and software configuration](#supported-hardware-and-software-configuration)
- [Runtime defaults](#runtime-defaults)
- [DSP control enablement](#dsp-control-enablement)
- [Transceiver operation](#transceiver-operation)
- [Pre-integration checks](#pre-integration-checks)
- [Current operational limitations](#current-operational-limitations)
- [Evidence retention](#evidence-retention)

## Purpose

This document collects the cross-subsystem configuration that an operator or integrator must know. It does not replace subsystem build instructions or troubleshooting records.

## Supported hardware and software configuration

| Area | Current repository-supported configuration |
|---|---|
| NRF hardware | Nordic nRF52833 DK, verified from FICR on the two physical boards used in bring-up |
| Zephyr board target | `nrf52833dk/nrf52833` |
| nRF Connect SDK used in bring-up | v3.2.3 |
| NRF host serial | 115200 baud, 8N1 |
| BLE default | LE Coded S=8 extended advertising/scanning |
| BLE alternate | LE 1M, runtime-switchable |
| DSP serial selection | automatic discovery from USB metadata; unambiguous candidate required |
| DSP classifier state | placeholder mode remains enabled in current implementation |
| Jackal bridge | not implemented |
| ROS arbiter | not implemented |

The earlier nRF52840 target was a hardware-identification error and caused an SRAM overrun before `main()`. Current instructions and validation use nRF52833 only.

## Runtime defaults

A freshly booted Transceiver starts:

- role: **TX**;
- PHY: **LE Coded S=8**;
- state latch: **CLR**.

Button behavior:

- Button 1 / `sw0`: switch PHY between Coded S=8 and LE 1M;
- Button 2 / `sw1`: switch runtime role TX <-> RX.

LED intent:

- TX: two role LEDs blink;
- RX: one role LED blinks;
- separate PHY LED on = Coded S=8, off = 1M.

The role/PHY logic is implemented; the complete human-observed LED and dedicated button-validation matrix remains open.

## DSP control enablement

The current DSP application may continue sensing when no unambiguous NRF serial console is found. In that case the serial control path is disabled rather than guessed.

The classifier currently runs with `PLACEHOLDER_MODE = True`. Normal experiment serial output is refused in that state. The development-only placeholder override exists for integration testing and must not be treated as evidence that the classifier is suitable for real corridor control.

There is no manual serial-port mode in the current DSP design; discovery is automatic by design.

## Transceiver operation

Build and flashing details live in [`../firmware/README.md`](../firmware/README.md). The system-level operational expectations are:

1. use the correct nRF52833 target;
2. flash the same image to both boards;
3. allow one board to remain TX and switch the other to RX;
4. keep both on the same PHY;
5. ensure only the intended process owns each serial console;
6. verify `OBS`/`CLR` transitions before connecting the path to robot motion.

Windows COM numbers are not stable identities and changed during bring-up. Re-resolve the intended board/interface rather than encoding the dated `COM14`/`COM8` observations into automation.

## Pre-integration checks

Before any full-system attempt, confirm:

- trained detector and label mapping are installed;
- placeholder protection is no longer the reason serial is blocked;
- live DSP -> physical TX transition has been validated;
- two-board link is on the intended common PHY;
- RX host path is producing the expected transitions;
- Jackal Ethernet/SSH path is reachable;
- local ROS STOP arbitration is implemented and tested independently;
- distance source/threshold are implemented and calibrated;
- communication-loss behavior is defined;
- the physical emergency stop is available and supervised.

If any downstream control item above is absent, the run is a subsystem/integration test, not an end-to-end controlled-robot experiment.

## Current operational limitations

- No experiment-valid trained detector is represented by the current placeholder-mode configuration.
- No complete DSP-to-TX hardware validation exists yet.
- No Jackal serial-to-SSH bridge exists in repository code.
- No Jackal ROS arbitration implementation exists.
- No distance-to-corner implementation or threshold exists.
- No end-to-end recovery/liveness policy exists.
- No full-chain acceptance run exists.

## Evidence retention

Dated hardware evidence belongs under the owning subsystem's validation area or under `sessions/` when it is session-specific. System-level validation claims must link back to that evidence instead of copying unverifiable conclusions into multiple files.
