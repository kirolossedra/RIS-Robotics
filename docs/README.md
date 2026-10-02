# RIS-Robotics Documentation

## Contents

- [Purpose](#purpose)
- [Documentation model](#documentation-model)
- [Source-of-truth hierarchy](#source-of-truth-hierarchy)
- [Maturity vocabulary](#maturity-vocabulary)
- [Stub and placeholder rule](#stub-and-placeholder-rule)
- [Evidence placement](#evidence-placement)
- [Directory map](#directory-map)
- [Maintenance rules](#maintenance-rules)

## Purpose

This directory is the canonical knowledge architecture for RIS-Robotics. It separates **what the system is**, **what it can do**, **why it was designed that way**, **what has been proven**, and **how it is operated**.

Implementation folders remain implementation folders. Raw hardware evidence, troubleshooting media, executable validation utilities, and dated engineering logs stay close to their owning subsystem and are linked from here rather than duplicated.

## Documentation model

```text
ARCHITECTURE  -> what the system is and how parts relate
FEATURES      -> what capabilities the system exposes
DECISIONS     -> why important choices were made
IMPLEMENTATION-> dsp/ firmware/ robotics/
VALIDATION    -> what behavior has actually been demonstrated

EXPERIMENTS   -> research questions, protocols, campaigns
OPERATIONS    -> how to configure/run the system
TROUBLESHOOTING -> known faults, diagnoses, recoveries
SESSIONS      -> chronological engineering history and evidence
```

Architecture, features, and decisions are deliberately different:

- **Architecture** owns structure, boundaries, interactions, state ownership, deployment, and safety authority.
- **Features** own observable capabilities and their current maturity.
- **Decisions** own rationale and historical alternatives; a decision does not prove implementation.

## Source-of-truth hierarchy

When records disagree, use this order:

1. current implementation/configuration for what code actually does;
2. dated validation evidence for what has actually been demonstrated;
3. accepted decision records for what the team chose;
4. canonical documents under `docs/` for the synthesized current model;
5. session logs and superseded records for historical reconstruction.

A document may be authoritative for its question without being evidence that the behavior works.

## Maturity vocabulary

| Status | Meaning |
|---|---|
| **Implemented** | Real implementation exists. |
| **Validated** | Direct software/hardware evidence demonstrates the stated behavior. |
| **Stub** | Deliberate controllable substitute exercises an interface or downstream process without claiming the real upstream behavior. |
| **Placeholder** | Temporary implementation/artifact occupies a production-shaped slot but is not semantically valid for the intended experiment. |
| **Blocked** | Implementation exists but cannot be used for the intended experiment because a prerequisite is missing. |
| **Design only** | Accepted architecture exists but implementation does not. |
| **TBD** | Mechanism/value has not been selected. |
| **Historical** | Accurate record of an earlier state, not current authority. |

Statuses may combine. For example, an RX stub can be **Implemented + Validated + Stub**. The classifier can be **Implemented + Placeholder + Blocked**.

## Stub and placeholder rule

Stubs are first-class system-process tools, not undocumented shortcuts.

Every stub must state:

- the real boundary it substitutes for;
- how the stub is activated;
- what downstream behavior it is allowed to validate;
- what it **cannot** prove;
- how operators can distinguish stub mode from natural/real mode;
- which validation evidence covers the stub itself.

A stub must never silently upgrade the maturity of the real path it replaces.

A placeholder is different: it fills a real implementation slot but lacks valid experiment semantics. Placeholder output must not be cited as evidence for the intended behavior.

## Evidence placement

Raw evidence remains with its owner:

- firmware hardware records and executable smoke tests: `firmware/validation/`;
- DSP implementation-specific tests and algorithm evidence: `dsp/tests/` and `dsp/docs/`;
- robot hardware troubleshooting and images: `robotics/`;
- chronological debug/session artifacts: `sessions/`.

`docs/validation/` synthesizes and indexes that evidence. It does not duplicate raw logs or test scripts.

## Directory map

| Directory | Authority |
|---|---|
| [`architecture/`](architecture/) | Structure, boundaries, interactions, runtime state, deployment, safety |
| [`features/`](features/) | Capabilities and feature maturity |
| [`decisions/`](decisions/) | Engineering rationale and superseded choices |
| [`validation/`](validation/) | Validation synthesis and evidence map |
| [`experiments/`](experiments/) | Research protocols and campaigns |
| [`operations/`](operations/) | Configuration and runbooks |
| [`troubleshooting/`](troubleshooting/) | Fault/recovery knowledge index |

The root-level `sessions/` remains the historical engineering journal because it also contains non-document debug evidence and scripts.

## Maintenance rules

- Every Markdown directory has an index `README.md`.
- Every Markdown document has a contents section.
- Do not put a capability description in architecture when it belongs in features.
- Do not put rationale in architecture when it belongs in a decision.
- Do not turn a session observation into a current claim until the owning canonical document is updated.
- Do not copy raw validation evidence into multiple places; link to it.
- Stubs, placeholders, design-only paths, and TBDs must remain visibly distinct.
- Product names belong in deployment bindings and hardware-specific evidence; architectural robot identities remain `DUMMY_ROBOT` and `CONTROLLED_ROBOT`.
