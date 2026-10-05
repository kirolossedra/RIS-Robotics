# Architecture

## Contents

- [Purpose](#purpose)
- [Architecture dimensions](#architecture-dimensions)
- [Rules](#rules)

## Purpose

Architecture describes **what the system is**, how responsibilities are partitioned, how components interact, and where state/control authority lives. It does not own feature rationale, experiment results, or troubleshooting history.

## Architecture dimensions

Each row is one immediate child directory. Follow its README for the next level of navigation where applicable.

| Directory | Architectural responsibility | What belongs there | Index |
|---|---|---|---|
| [`system/`](system/) | Whole-system definition | Overview, boundaries, current state, requirements/traceability, integration plan, progress, and system views | [`system/README.md`](system/README.md) |
| [`subsystems/`](subsystems/) | Stable functional decomposition | DSP, sensing, wireless transport, and robot-control responsibilities independent of current hardware bindings | [`subsystems/README.md`](subsystems/README.md) |
| [`interactions/`](interactions/) | Cross-boundary behavior | Interfaces, dependency/change-impact graph, data flow, and control flow | [`interactions/README.md`](interactions/README.md) |
| [`runtime/`](runtime/) | Dynamic system behavior | State machines, timing/liveness, and explicit stub/simulation boundaries | [`runtime/README.md`](runtime/README.md) |
| [`deployment/`](deployment/) | Physical realization | Topology and current role-to-hardware bindings | [`deployment/README.md`](deployment/README.md) |
| [`safety/`](safety/) | Control authority and containment | Motion authority, failure modes, and safety-policy boundaries | [`safety/README.md`](safety/README.md) |

## Rules

- Architecture uses roles and functional subsystems, not replaceable product names.
- Current hardware choices belong under deployment.
- A stub may appear in runtime architecture, but it must be marked **Stub** and may not masquerade as the real path.
- Validation claims belong under `docs/validation/` and raw evidence remains with its owner.
