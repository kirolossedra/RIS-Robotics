# System Validation

## Contents

- [Purpose](#purpose)
- [Validation ladder](#validation-ladder)
- [DSP evidence](#dsp-evidence)
- [Firmware and BLE evidence](#firmware-and-ble-evidence)
- [Robot-side evidence](#robot-side-evidence)
- [Not yet proven](#not-yet-proven)
- [End-to-end acceptance record](#end-to-end-acceptance-record)

## Purpose

This document lists evidence, not intentions. A successful build is not called a hardware pass, and a subsystem smoke test is not called an end-to-end system validation.

## Validation ladder

1. **Static/build evidence** — code compiles/configuration is internally coherent.
2. **Hardware-free behavior tests** — deterministic logic exercised without target hardware.
3. **Single-device bring-up** — target boots and core interfaces are alive.
4. **Link/subsystem hardware test** — multiple components interoperate across the real boundary.
5. **Integrated subsystem test** — upstream implementation drives downstream hardware.
6. **End-to-end system test** — sensing event changes Controlled Robot motion through the complete safety path.

The repository has reached level 4 for the NRF transport, but not level 6 for the complete experiment.

## DSP evidence

- `dsp/tests/test_realtime_detection.py` documents 14 hardware-free checks covering capture lifecycle, voting behavior, output mapping, 10-frame window cadence, warm-up isolation, Capon equivalence, and GUI behavior.
- `dsp/tests/test_serial_integration.py` exercises the obstacle-state FSM, exact serial framing, no-write cases, failure surfacing, and retry semantics using an injected fake stream.
- The DSP integration code is wired after `vote_predictions()` and before display.
- Serial discovery is defensive: ambiguous/no candidate returns no device and leaves the sensing application usable.

**Gap:** the live DSP-to-physical-NRF-TX boundary has not yet been validated, and the model is still placeholder-mode, so no experiment-valid control claim is made.

## Firmware and BLE evidence

### Single-board bring-up — PASS

`../firmware/validation/2026-09-28-single-board-bringup.md` records physical target identification as nRF52833, corrected build/flash, clean boot, and SWD/UART/GPIO evidence consistent with successful startup.

### Two-board S=8 smoke test — PASS

`../firmware/validation/2026-09-28-two-board-smoke-test.md` records two nRF52833 DKs on the same image: repeated `OBS` produced exactly one RX `OBS`, repeated `CLR` produced exactly one RX `CLR`, and a later obstacle episode produced one new RX `OBS` on default Coded S=8.

The run observed TX `COM14` and RX `COM8`; those are dated observations, not persistent device identities.

## Robot-side evidence

`../robotics/` contains real hardware/connectivity troubleshooting. Those records establish operational knowledge, but they do **not** validate the target Controlled Robot serial->SSH->ROS STOP path.

## Not yet proven

- trained detector behavior for the actual corridor classes;
- live DSP semantic transition -> physical TX serial command;
- `rx_logger.py` JSONL on physical RX;
- dedicated Button-1 PHY switching over air;
- dedicated Button-2 role switching validation;
- LE 1M end-to-end link behavior;
- range/reliability characterization;
- persistent serial->SSH bridge and reconnect semantics;
- local ROS STOP precedence over joystick commands;
- distance measurement/gating;
- stale/loss behavior;
- complete sensing->Controlled Robot STOP latency and reliability.

## End-to-end acceptance record

**Current state: no end-to-end acceptance run exists.**

A future acceptance record should capture revisions, physical topology, selected PHY, trained model identity, distance source/threshold, timestamps at meaningful boundaries, Controlled Robot command output, failure-injection results, and physical emergency-stop supervision.
