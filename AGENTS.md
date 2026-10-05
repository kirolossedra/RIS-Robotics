# Agent Guidance

## Contents

- [Documentation](#documentation)
- [Workflow](#workflow)

## Documentation

- The canonical documentation control center is `docs/README.md`.
- Architecture, features, decisions, validation, experiments, operations, and troubleshooting are separate document classes.
- Every Markdown directory must have a `README.md` index and every Markdown document must have a contents section.
- Every directory README that owns child directories must include a child-directory guide. The guide must document every immediate child directory, state its purpose and what belongs there, and link to that child's `README.md` when one exists.
- README navigation is recursive: each child README documents its own immediate child directories. Do not duplicate an entire descendant tree into every ancestor README.
- A child directory that itself contains subdirectories must have its own `README.md` so recursive traversal never dead-ends. A leaf directory needs no synthetic subtree description.
- When a directory is added, removed, renamed, or repurposed, update its parent README in the same change.
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
