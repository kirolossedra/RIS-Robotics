# Agent Guidance

## Contents

- [Documentation](#documentation)
- [Workflow](#workflow)

## Documentation

- The canonical documentation control center is `docs/README.md`.
- Architecture, features, decisions, validation, experiments, operations, and troubleshooting are separate document classes.
- Every Markdown directory must have a `README.md` index and every Markdown document must have a contents section.
- Do not use Husky/Jackal as architectural component identities; use `DUMMY_ROBOT` and `CONTROLLED_ROBOT`. Product names belong in deployment bindings and hardware-specific evidence.
- Treat **Stub**, **Placeholder**, **Design only**, **TBD**, **Implemented**, and **Validated** as distinct maturity concepts.
- A stub-only pass must never be reported as validation of the real path it replaces.
- Preserve superseded decisions and dated evidence; do not erase engineering history.
- Raw evidence stays with the owning subsystem/session and canonical documents link to it rather than copying it.

## Workflow

- Before changing a cross-system interface, inspect `docs/architecture/interactions/dependencies.md`.
- Update the feature document when observable capability or maturity changes.
- Update validation synthesis only when evidence exists.
- Update architecture only when structure, ownership, interfaces, runtime semantics, deployment, or safety authority changes.
- Do not change repository or branch without explicit user approval.
