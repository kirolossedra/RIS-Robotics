# Decision: Robot-Role Abstraction and Hardware Binding

**ID:** `robot-runtime-0003`  
**Status:** Accepted — current architecture rule  
**Date:** 2026-10-02  
**Scope:** Separation of stable robot roles from replaceable physical-platform bindings

## Contents

- [Context](#context)
- [Decision](#decision)
- [Canonical role symbols](#canonical-role-symbols)
- [Current hardware bindings](#current-hardware-bindings)
- [Documentation rule](#documentation-rule)
- [Consequences](#consequences)
- [Relationship to earlier decisions](#relationship-to-earlier-decisions)

## Context

The repository had begun to use **Husky** and **Jackal** as if those product names were architectural components. That makes a replaceable hardware choice look like a system invariant and forces platform-selection history into architecture, interfaces, requirements, and control semantics.

The actual system concepts are the roles played by the two robots.

## Decision

The architecture SHALL model robots through two stable roles:

- **Dummy Robot** — the physical robot target/stimulus in the conflicting or hidden corridor.
- **Controlled Robot** — the robot whose normal motion is subject to the local higher-priority STOP rule.

The physical product assigned to either role is a **hardware binding**. Changing a binding does not, by itself, change the system architecture.

Architecture, interfaces, requirements, runtime/state semantics, safety/control rules, and integration plans therefore refer to the roles rather than directly to Husky or Jackal.

## Canonical role symbols

The repository uses the following macro-like architectural identifiers when an unambiguous symbolic name is useful:

```text
DUMMY_ROBOT
CONTROLLED_ROBOT
```

Their human-readable names are **Dummy Robot** and **Controlled Robot**.

These are documentation/system-model symbols, not C preprocessor macros and not new runtime configuration variables.

## Current hardware bindings

| Architectural role | Canonical symbol | Current hardware binding |
|---|---|---|
| Dummy Robot | `DUMMY_ROBOT` | Clearpath Husky A200 |
| Controlled Robot | `CONTROLLED_ROBOT` | Clearpath Jackal |

These bindings are current experiment choices, not permanent architectural identities.

## Documentation rule

Product names remain appropriate when the document is specifically about the product or physical deployment, including:

- hardware-selection/binding decisions;
- platform-specific setup and operations;
- hardware validation evidence;
- troubleshooting records;
- dated session/history records.

Product names SHALL NOT be used as the primary component identity in:

- system architecture;
- interface contracts;
- system requirements;
- generic runtime/state models;
- safety/control semantics;
- dependency/integration descriptions.

When a physical detail matters in one of those system documents, the role is named first and the current binding may be stated explicitly as supporting deployment context.

## Consequences

- Replacing the Dummy Robot platform does not require rewriting the sensing/control architecture.
- Replacing the Controlled Robot platform does not require renaming the downstream control subsystem; only its binding-specific integration and validation need to change.
- Hardware-specific evidence stays precise instead of being artificially generalized.
- Architectural diagrams become statements about responsibilities rather than an accidental inventory of currently available products.
- New implementation work should ask whether it belongs to a **role contract** or to a **specific hardware binding** before documenting it.

## Relationship to earlier decisions

- `robot-runtime-0001` remains the record of how the currently available Clearpath platforms were assigned to the two roles. Its product assignment is retained as the current hardware binding, while its hard-coded architectural naming is superseded by this decision.
- `robot-runtime-0002` remains valid as the hardware-specific Dummy Robot / Radar acquisition configuration for the current Husky A200 binding.
- `robot-ros-0001` remains valid in substance, but its control path is now expressed as a **Controlled Robot** bridge/arbitration architecture; Clearpath Jackal is the current binding.

No historical troubleshooting, validation, or session evidence is rewritten by this decision.
