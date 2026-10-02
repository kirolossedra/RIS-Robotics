# Architecture

## Contents

- [Purpose](#purpose)
- [Architecture dimensions](#architecture-dimensions)
- [Rules](#rules)

## Purpose

Architecture describes **what the system is**, how responsibilities are partitioned, how components interact, and where state/control authority lives. It does not own feature rationale, experiment results, or troubleshooting history.

## Architecture dimensions

- [`system/`](system/) — whole-system overview, boundaries, requirements, current state.
- [`subsystems/`](subsystems/) — stable functional decomposition independent of current product bindings.
- [`interactions/`](interactions/) — interfaces, dependencies, data flow, and control flow.
- [`runtime/`](runtime/) — state machines, liveness, timing, stubs/simulation boundaries.
- [`deployment/`](deployment/) — physical topology and current hardware bindings.
- [`safety/`](safety/) — motion authority, failure containment, and unresolved safety policy.

## Rules

- Architecture uses roles and functional subsystems, not replaceable product names.
- Current hardware choices belong under deployment.
- A stub may appear in runtime architecture, but it must be marked **Stub** and may not masquerade as the real path.
- Validation claims belong under `docs/validation/` and raw evidence remains with its owner.
