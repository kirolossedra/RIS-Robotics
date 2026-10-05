# RIS-Robotics

Repository for the Radar/RIS-to-robot experiment that turns a sensed corridor condition into a compact control state and, ultimately, a locally enforced Controlled Robot STOP.

**System documentation status:** audited against the implementation on 2026-09-28. The repository is currently validated through the two-board NRF/BLE transport; the Controlled Robot actuation path is not yet implemented end to end.

## Contents

- [System at a glance](#system-at-a-glance)
- [Robot-role abstraction and current bindings](#robot-role-abstraction-and-current-bindings)
- [Current implementation status](#current-implementation-status)
- [Documentation](#documentation)
- [Repository areas](#repository-areas)
- [System invariants](#system-invariants)
- [What remains](#what-remains)

## System at a glance

```text
DUMMY_ROBOT / Dummy Robot
    -> Radar/RIS sensing
    -> central laptop DSP
       acquisition -> maps -> CNN-LSTM -> rolling vote
       -> obstacle-state adapter -> OBS/CLR serial
    -> nRF52833 Transceiver (TX role)
    -> BLE extended advertising
       Coded S=8 default; LE 1M switchable
    -> nRF52833 Transceiver (RX role)
    -> OBS/CLR serial
    -> Controlled Robot-side control bridge                  [PENDING]
    -> persistent SSH / robot-side ROS interface   [PENDING]
    -> distance-gated local STOP arbitration       [PENDING]
    -> CONTROLLED_ROBOT / Controlled Robot
```

The system architecture is expressed in stable robot roles rather than product names: **Dummy Robot** and **Controlled Robot**. Hardware selection is a binding of those roles, not the identity of the roles themselves.

## Robot-role abstraction and current bindings

| Architectural role | Canonical symbol | Current hardware binding |
|---|---|---|
| Dummy Robot | `DUMMY_ROBOT` | Clearpath Husky A200 |
| Controlled Robot | `CONTROLLED_ROBOT` | Clearpath Jackal |

Architecture, interfaces, requirements, and control semantics use the role names/symbols. Product names belong in hardware-binding decisions, deployment/operations, hardware validation, troubleshooting, and historical evidence.

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
| Controlled Robot-side serial -> persistent SSH bridge | Design accepted | Not implemented in repository |
| ROS STOP arbitration | Design accepted | Not implemented in repository |
| Distance-to-corner source + `DISTANCE_THRESHOLD` | Required by design | **TBD** |
| Full sensing -> Controlled Robot STOP chain | Target architecture | Not yet integrated or validated end to end |

## Documentation

The canonical documentation control center is [`docs/README.md`](docs/README.md). It separates architecture, features, decisions, validation, experiments, operations, and troubleshooting, while keeping raw implementation evidence with the subsystem that produced it.

The concise boundary-by-boundary progress view is [`docs/architecture/system/progress.md`](docs/architecture/system/progress.md).

Start with:

- [`docs/architecture/`](docs/architecture/) — what the system is and how its parts relate.
- [`docs/features/`](docs/features/) — what capabilities the system provides, including stub/placeholder/design maturity.
- [`docs/decisions/`](docs/decisions/) — why significant engineering choices were made.
- [`docs/validation/`](docs/validation/) — what has actually been demonstrated, linked to raw evidence.
- [`docs/experiments/`](docs/experiments/) — research campaigns and protocols.
- [`docs/operations/`](docs/operations/) — how to configure and operate the system.
- [`docs/troubleshooting/`](docs/troubleshooting/) — fault/recovery knowledge and hardware-specific investigation indexes.

The legacy [`system/`](system/) and [`decision-logs/`](decision-logs/) paths are retained only as compatibility entry points during the migration.

## Repository areas

- [`dsp/`](dsp/) — radar acquisition, feature construction, CNN-LSTM adapter, rolling vote, GUI, obstacle-state adapter, serial discovery/output, and tests.
- [`firmware/`](firmware/) — shared Transceiver firmware, host RX logger, build/flash instructions, and dated validation evidence.
- [`robotics/`](robotics/) — robot-side connectivity, access, controller, and troubleshooting records.
- [`docs/`](docs/) — canonical engineering knowledge: architecture, features, decisions, validation, experiments, operations, and troubleshooting.
- [`sessions/`](sessions/) — dated engineering-session evidence and debug artifacts; historical logs are evidence, not current architecture authority.
- [`system/`](system/) and [`decision-logs/`](decision-logs/) — compatibility paths retained while canonical documents live under `docs/`.

## System invariants

- A missing, unknown, failed, or silent sensing result is **not** equivalent to corridor clear.
- Placeholder inference must not drive experiment control; the code refuses serial output in placeholder mode unless a development-only override is explicitly used.
- The NRF link carries compact `OBS`/`CLR` state, not raw radar data.
- The Controlled Robot-side STOP priority must be enforced locally by robot-side arbitration; message arrival order is not a safety policy.
- Distance-to-corner is gating context, not a third motion authority.
- The software STOP is an experiment mechanism and does not replace the physical emergency stop or supervised lab procedure.

## What remains

The next system milestone is not more BLE work. It is to make the sensing output experiment-valid, validate the DSP-to-TX serial boundary on hardware, then implement and validate the Controlled Robot-side bridge, local ROS arbitration, and distance gate before attempting the full end-to-end run.
