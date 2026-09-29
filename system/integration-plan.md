# System Integration Plan

## Contents

- [Purpose](#purpose)
- [Dependency order](#dependency-order)
- [Stage 1 — make sensing semantics experiment-valid](#stage-1--make-sensing-semantics-experiment-valid)
- [Stage 2 — close the DSP-to-TX hardware boundary](#stage-2--close-the-dsp-to-tx-hardware-boundary)
- [Stage 3 — finish NRF host-side validation](#stage-3--finish-nrf-host-side-validation)
- [Stage 4 — implement the Jackal bridge](#stage-4--implement-the-jackal-bridge)
- [Stage 5 — implement local ROS arbitration](#stage-5--implement-local-ros-arbitration)
- [Stage 6 — implement distance gating](#stage-6--implement-distance-gating)
- [Stage 7 — validate failures before the full demo](#stage-7--validate-failures-before-the-full-demo)
- [Stage 8 — end-to-end integration](#stage-8--end-to-end-integration)
- [Exit criteria](#exit-criteria)

## Purpose

This plan orders remaining work by dependency. It avoids spending effort on downstream polish before the upstream control semantics are trustworthy.

## Dependency order

```text
trained detector
 -> live DSP serial boundary
 -> confirmed NRF host behavior
 -> Jackal serial/SSH bridge
 -> local ROS arbitration
 -> distance source + threshold
 -> loss/stale-state policies
 -> end-to-end experiment
```

## Stage 1 — make sensing semantics experiment-valid

- Replace the placeholder model with the trained detector intended for the experiment.
- Define the authoritative output-index -> label mapping.
- Set `PLACEHOLDER_MODE = False` only after the model/mapping are correct.
- Re-run DSP tests and confirm person/robot/nothing semantics match the real experiment.

**Exit:** the system can justify `OBS` and `CLR` semantically, not just mechanically.

## Stage 2 — close the DSP-to-TX hardware boundary

- Run the real acquisition/classification path with the physical TX board connected.
- Confirm auto-discovery selects the intended console without manual port configuration.
- Induce controlled semantic transitions and verify exact `OBS`/`CLR` delivery at the TX boundary.
- Confirm serial failure remains visible and does not fabricate `CLR`.

**Exit:** live DSP state has been observed driving the physical TX board correctly.

## Stage 3 — finish NRF host-side validation

- Run `firmware/tools/rx_logger.py` on physical RX and preserve JSONL evidence.
- Validate Button-2 role switching deliberately on hardware.
- Validate coordinated Button-1 S=8 <-> 1M switching over air.
- Characterize range/reliability only to the level required by the corridor experiment.

**Exit:** the chosen experiment transport mode and host output are reproducible.

## Stage 4 — implement the Jackal bridge

- Add the RX serial consumer on the Jackal-side host.
- Maintain one persistent SSH session over Ethernet rather than reconnecting per event.
- Make connection state observable.
- Define reconnect and state-resynchronization behavior explicitly.
- Keep the bridge responsible for transport, not motion-policy precedence.

**Exit:** `OBS`/`CLR` can be delivered reproducibly to the Jackal onboard computer without making the laptop the arbiter.

## Stage 5 — implement local ROS arbitration

- Identify the actual Jackal ROS command path and existing teleoperation topic flow.
- Insert a local supervisor/mux/arbiter so STOP has explicit precedence over normal `cmd_vel`.
- Test STOP assertion/release independently of Radar/RIS.
- Verify message timing cannot bypass precedence.

**Exit:** a local test input can reliably force zero motion and return control according to policy.

## Stage 6 — implement distance gating

- Select the distance-to-corner source.
- Define units, update rate, validity/staleness criteria, and calibration.
- Select `DISTANCE_THRESHOLD` from experiment geometry rather than convenience.
- Combine distance validity with obstacle state inside the local arbitration layer.

**Exit:** `unsafe AND near_corner -> STOP` is implemented and testable.

## Stage 7 — validate failures before the full demo

Exercise serial disconnect, BLE loss/silence, SSH loss, stale distance, unknown classifier output, process restart, and reconnect/resynchronization. Record the behavior actually implemented. Do not infer a safe/clear state merely because one transport stopped producing messages.

## Stage 8 — end-to-end integration

Run the complete Husky -> Radar/RIS -> DSP -> NRF -> Jackal chain under supervised lab conditions. Capture timestamps at meaningful boundaries so latency and failure behavior can be reconstructed.

## Exit criteria

The project can be called system-integrated only when the complete control path is implemented, failure semantics are explicit, end-to-end evidence exists, and physical emergency-stop supervision remains part of the procedure.
