# Failure Modes and Safety

## Contents

- [Purpose](#purpose)
- [Safety boundary](#safety-boundary)
- [Failure-mode ledger](#failure-mode-ledger)
- [Current protective behavior](#current-protective-behavior)
- [Unresolved safety policies](#unresolved-safety-policies)
- [Rules for future implementation](#rules-for-future-implementation)

## Purpose

This document names failure modes that cross subsystem boundaries. It does not claim the research software is a certified safety system.

## Safety boundary

The software STOP is an experiment-level intervention. It does not replace the Jackal physical emergency stop, supervised laboratory operation, or ordinary procedures for keeping people clear of uncontrolled robot motion.

## Failure-mode ledger

| Failure | Current behavior | Risk if misinterpreted | Status |
|---|---|---|---|
| Placeholder classifier used | Serial experiment output refused by default | False obstacle/clear semantics | Protected in code |
| Unknown classifier label | Adapter holds prior state and faults; GUI may abort | Unknown treated as clear | Protected at adapter |
| Radar/acquisition/inference exception | Run exits/partial save behavior; no synthetic clear | Stale downstream state | Downstream policy still needed |
| Serial device missing/ambiguous | Serial disabled; sensing can continue | Operator assumes robot path is active | Visible warning; operational check needed |
| Serial write failure | Writer reports failure and keeps last-transmitted stale for retry | Lost state transition | Retry behavior implemented; system watchdog absent |
| TX receives malformed line | Ignored; latch unchanged | Silent command loss | Firmware behavior defined |
| BLE packet duplicate | RX suppresses duplicate transition | Event flood | Validated |
| BLE silence/link loss | RX emits nothing | Silence mistaken for clear | **System policy unresolved** |
| RX host process stops | No downstream event | Stale state | **Policy unresolved** |
| SSH loss | Bridge does not yet exist | Control state cannot reach robot | **Implementation + policy pending** |
| ROS arbiter absent | STOP precedence does not exist | Robot remains under normal teleop only | **Not implemented** |
| Distance stale/invalid | No implementation exists | Gate may be wrong | **TBD** |
| Wrong Zephyr target | Previously caused pre-main BusFault | Firmware unavailable | Root cause fixed/documented; use nRF52833 target |
| Role/PHY mismatch | No useful wireless propagation | Apparent link loss | Indicators exist; dedicated switch validation remains open |

## Current protective behavior

The strongest existing protections are at the DSP boundary: placeholder output is guarded, ambiguous serial discovery does not guess, invalid semantic labels do not become `CLR`, and serial write errors are surfaced rather than hidden.

The firmware also defaults to a defined `CLR` latch, validates BLE service-data structure, suppresses repeated RX transitions, and uses visible role/PHY indication.

These protections are useful but they do not solve downstream liveness. Once robot motion depends on remote state, the system needs an explicit policy for stale or missing data.

## Unresolved safety policies

The repository does **not** yet define:

- maximum acceptable age of obstacle state;
- what the Jackal must do after BLE silence;
- what the Jackal must do after SSH loss;
- how a restarted bridge learns the authoritative current state;
- what happens when distance is unavailable or stale;
- whether STOP is latched through any failures and, if so, how it is released;
- end-to-end latency/reliability acceptance thresholds.

These must be implemented consciously. Choosing a behavior only because it is easy to code would turn a transport accident into a motion policy.

## Rules for future implementation

- **Never convert absence of evidence into `CLR`.**
- Keep final motion precedence local to the Jackal.
- Make connectivity/liveness observable to the operator.
- Define state age and reconnect semantics before relying on the bridge.
- Separate transport retries from semantic state transitions.
- Validate failure behavior with the same seriousness as nominal `OBS`/`CLR` propagation.
- Retain the physical emergency-stop path regardless of software maturity.
