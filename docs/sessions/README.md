# Sessions

## Authority boundary

Sessions are chronological engineering history and may contain debug scripts, logs, temporary test conditions, and observations. They are evidence, not current architecture authority.

Canonical current knowledge lives in the other sections of `docs/`. When a session changes architecture, feature maturity, a decision, or validation status, the corresponding canonical document must be updated separately.

## Session layout

One folder per engineering date, each self-contained: the session log, a full investigation summary, and that date's debug evidence when such evidence exists. Each session README continues recursively into any child evidence directory.

| Directory | Session scope | Child structure | Index |
|---|---|---|---|
| [`2026-10-04/`](2026-10-04/) | Recursive system-progress documentation and protocol documentation work | `CODEX_SESSION_LOG.md` plus `debug-evidence/` | [`2026-10-04/README.md`](2026-10-04/README.md) |
| [`2026-10-02/`](2026-10-02/) | Husky 1 bring-up and Joystick 3 Bluetooth recurrence | Session summary and `MUSE_SESSION_LOG.md`; no child directory | [`2026-10-02/README.md`](2026-10-02/README.md) |
| [`2026-09-28/`](2026-09-28/) | J-Link recovery, Transceiver firmware, nRF52833 bring-up, and two-board link | `MUSE_SESSION_LOG.md` plus `debug-evidence/` | [`2026-09-28/README.md`](2026-09-28/README.md) |

Convention: `docs/sessions/<YYYY-MM-DD>/` holds `README.md` (investigation summary), an agent-named `<AGENT>_SESSION_LOG.md` (chronological record), and, when produced, `debug-evidence/` (raw artifacts). Existing MUSE-prefixed logs are historical; Codex sessions use `CODEX_SESSION_LOG.md`. Records are append-only history.
