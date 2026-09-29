# RIS-Robotics

Repository for the Radar/RIS-to-robot experiment that turns a sensed corridor condition into a compact control state and, ultimately, a locally enforced Jackal STOP.

**System documentation status:** audited against the implementation on 2026-09-28. The repository is currently validated through the two-board NRF/BLE transport; the Jackal actuation path is not yet implemented end to end.

## Contents

- [System at a glance](#system-at-a-glance)
- [Current implementation status](#current-implementation-status)
- [Documentation](#documentation)
- [Repository areas](#repository-areas)
- [System invariants](#system-invariants)
- [What remains](#what-remains)

## System at a glance

```text
Husky / Dummy Robot
    -> Radar/RIS sensing
    -> central laptop DSP
       acquisition -> maps -> CNN-LSTM -> rolling vote
       -> obstacle-state adapter -> OBS/CLR serial
    -> nRF52833 Transceiver (TX role)
    -> BLE extended advertising
       Coded S=8 default; LE 1M switchable
    -> nRF52833 Transceiver (RX role)
    -> OBS/CLR serial
    -> Jackal-side control bridge                  [PENDING]
    -> persistent SSH / robot-side ROS interface   [PENDING]
    -> distance-gated local STOP arbitration       [PENDING]
    -> Jackal / Controlled Robot
```

The two robots have separate roles: the **Husky is the Dummy Robot** in the conflicting/hidden corridor; the **Jackal is the Controlled Robot** in the controlled corridor.

## Current implementation status

| Area | Repository reality | Validation state |
|---|---|---|
| Radar acquisition + DSP feature pipeline | Implemented | Software-tested; real sensing code exists |
| CNN-LSTM classification path | Implemented structurally, but `PLACEHOLDER_MODE = True` | Not valid for experiment control until the trained detector and label mapping are installed |
| Voted label -> obstacle state -> serial `OBS`/`CLR` | Implemented in `dsp/integration/` and wired into `record_frames()` | Hardware-free tests exist; serial-to-NRF validation from the live DSP path remains open |
| Serial device discovery | Implemented; unambiguous auto-detection only | Ambiguous/failure cases disable serial instead of guessing |
| Shared NRF Transceiver firmware | Implemented as one nRF52833 image with runtime TX/RX roles | Correct-target boot validated on hardware |
| NRF TX -> BLE -> NRF RX | Implemented | **Two-board smoke test PASS** on 2026-09-28 for `OBS`/`CLR`, duplicate suppression, S=8, and UART integration |
| RX JSONL logger | Implemented | Standalone hardware run still open |
| Jackal-side serial -> persistent SSH bridge | Design accepted | Not implemented in repository |
| ROS STOP arbitration | Design accepted | Not implemented in repository |
| Distance-to-corner source + `DISTANCE_THRESHOLD` | Required by design | **TBD** |
| Full sensing -> Jackal STOP chain | Target architecture | Not yet integrated or validated end to end |

## Documentation

The system-level control center is [`system/README.md`](system/README.md). It separates **implemented**, **validated**, **blocked**, **design-only**, and **TBD** work instead of treating the intended end state as current behavior.

Key system records:

- [`system/architecture.md`](system/architecture.md) — physical/logical topology, responsibilities, boundaries, and non-goals.
- [`system/interfaces.md`](system/interfaces.md) — contracts between DSP, serial, BLE, RX, and the not-yet-implemented Jackal side.
- [`system/runtime-and-state.md`](system/runtime-and-state.md) — state machines, latches, gating semantics, and runtime ownership.
- [`system/implementation-status.md`](system/implementation-status.md) — implementation maturity ledger tied to repository evidence.
- [`system/validation.md`](system/validation.md) — what has actually been proven and what has not.
- [`system/failure-modes-and-safety.md`](system/failure-modes-and-safety.md) — failure semantics and unresolved safety-critical policies.
- [`system/integration-plan.md`](system/integration-plan.md) — remaining work in dependency order.
- [`decision-logs/`](decision-logs/) — why architecture choices were made; decision acceptance does not imply implementation completion.

## Repository areas

- [`dsp/`](dsp/) — radar acquisition, feature construction, CNN-LSTM adapter, rolling vote, GUI, obstacle-state adapter, serial discovery/output, and tests.
- [`firmware/`](firmware/) — shared Transceiver firmware, host RX logger, build/flash instructions, and dated validation evidence.
- [`robotics/`](robotics/) — robot-side connectivity, access, controller, and troubleshooting records.
- [`system/`](system/) — repository-wide system documentation and integration truth.
- [`decision-logs/`](decision-logs/) — active and superseded architecture decisions.
- [`sessions/`](sessions/) — dated engineering-session evidence; historical logs are not the current architecture authority.

## System invariants

- A missing, unknown, failed, or silent sensing result is **not** equivalent to corridor clear.
- Placeholder inference must not drive experiment control; the code refuses serial output in placeholder mode unless a development-only override is explicitly used.
- The NRF link carries compact `OBS`/`CLR` state, not raw radar data.
- The Jackal-side STOP priority must be enforced locally by robot-side arbitration; message arrival order is not a safety policy.
- Distance-to-corner is gating context, not a third motion authority.
- The software STOP is an experiment mechanism and does not replace the physical emergency stop or supervised lab procedure.

## What remains

The next system milestone is not more BLE work. It is to make the sensing output experiment-valid, validate the DSP-to-TX serial boundary on hardware, then implement and validate the Jackal-side bridge, local ROS arbitration, and distance gate before attempting the full end-to-end run.
