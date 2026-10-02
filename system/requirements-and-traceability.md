# Requirements and Traceability

## Contents

- [Purpose](#purpose)
- [System requirements](#system-requirements)
- [Safety and failure requirements](#safety-and-failure-requirements)
- [Traceability rules](#traceability-rules)
- [Requirements without implementation](#requirements-without-implementation)

## Purpose

This document turns the system architecture into explicit, reviewable requirements and ties each requirement to the implementation and evidence that currently support it. It deliberately uses descriptive names rather than invented requirement codes.

## System requirements

| Requirement | Current implementation | Verification / evidence | Status |
|---|---|---|---|
| The Dummy Robot acts only as the moving target in the conflicting corridor. | Experiment architecture and robot decision records | Dummy Robot acquisition/troubleshooting records | Accepted system role |
| The Controlled Robot remains normally teleoperated through its existing velocity-command path. | Robot architecture decision | Robot-side integrated validation not yet performed | Accepted; downstream integration pending |
| The sensing computer reduces Radar/RIS observations to a semantic person/robot/nothing decision before control transport. | DSP acquisition, classifier adapter, rolling vote | DSP software tests | Implemented; classifier semantics blocked by placeholder model |
| A stable person or robot decision maps to obstacle; stable nothing maps to clear. | `dsp/integration/obstacle_state.py` | `dsp/tests/test_serial_integration.py` | Implemented + software-tested |
| Unknown or invalid semantic input must not manufacture a clear state. | Obstacle-state adapter holds previous state and faults | Serial-integration tests | Implemented + software-tested |
| DSP-to-transceiver serial commands are exact transition-oriented `OBS`/`CLR` lines. | `dsp/integration/serial_output.py` + TX parser | Hardware-free serial tests; TX UART exercised independently | Implemented; live-DSP-to-TX validation pending |
| Serial device discovery must not guess when more than one plausible device is present. | `dsp/integration/serial_discovery.py` | Discovery tests / metadata checks | Implemented |
| Both NRF boards use the same firmware image and select TX/RX role at runtime. | `firmware/transceiver/` | Correct-target hardware bring-up; two-board link used runtime roles | Implemented; dedicated role-switch exercise still open |
| Default wireless transport is LE Coded S=8, with LE 1M available as a runtime mode. | Transceiver firmware | S=8 smoke test PASS; coordinated 1M switch test open | Partially hardware-validated |
| Repeated wireless state advertisements must not become repeated host transitions. | RX deduplication | Two-board smoke test with repeated `OBS`/`CLR` | Implemented + validated |
| The Controlled Robot-side host transports received state to the onboard computer through a persistent SSH session. | No bridge code yet | None | Design only |
| STOP precedence is enforced locally on the Controlled Robot rather than by message arrival order. | No ROS arbiter yet | None | Design only |
| STOP is enforced only when the corridor is unsafe and the Controlled Robot is within the configured corner-distance threshold. | No distance gate yet | None | Design only; distance source and threshold TBD |

## Safety and failure requirements

| Requirement | Current mechanism | Status |
|---|---|---|
| Placeholder inference must not drive experiment control by default. | Serial startup guard while `PLACEHOLDER_MODE = True` | Implemented |
| Transport silence must not be interpreted as proof of clear corridor state. | Documented invariant; no downstream liveness policy yet | Partially implemented; downstream policy pending |
| Serial write failure must remain observable and retryable rather than silently advancing transport state. | `last_transmitted` remains stale on failed write | Implemented + software-tested |
| BLE packets must match the expected service-data type, UUID, version, and length before state acceptance. | RX firmware validation | Implemented; exercised by successful real-link path |
| Communication-loss and stale-state behavior must be explicit before end-to-end readiness. | No complete downstream policy yet | Pending |
| Software STOP must not replace the physical emergency-stop path or supervised laboratory procedure. | Operational constraint | Required throughout testing |

## Traceability rules

A requirement is not considered satisfied merely because a design decision exists. For this repository:

1. **Architecture/decision** establishes intent.
2. **Implementation** establishes that the mechanism exists.
3. **Verification evidence** establishes what behavior has actually been demonstrated.
4. **System status** must reflect the weakest of those three stages for the claim being made.

When implementation changes, update this file together with [`implementation-status.md`](implementation-status.md) and [`validation.md`](validation.md) if the maturity claim changes.

## Requirements without implementation

The largest unimplemented requirements are all on the controlled-robot side: persistent serial-to-SSH forwarding, Controlled Robot-local ROS command arbitration, distance acquisition/gating, stale-state handling, reconnect/resynchronization, and the full-chain acceptance test. These are not documentation gaps; they are real engineering gaps.
