# Sessions

## Authority boundary

Sessions are chronological engineering history and may contain debug scripts, logs, temporary test conditions, and observations. They are evidence, not current architecture authority.

Canonical current knowledge lives in the other sections of `docs/`. When a session changes architecture, feature maturity, a decision, or validation status, the corresponding canonical document must be updated separately.

## Session layout

One folder per engineering date, each self-contained: the session log,
a full investigation summary, and that date's debug evidence.

- [`2026-10-04/`](2026-10-04/) — recursive system progress diagrams, written subsystem analysis, Mermaid status colors, and documentation commits. Start with its [`README.md`](2026-10-04/README.md).
- [`2026-10-02/`](2026-10-02/) — Husky 1 bring-up and Joystick 3 Bluetooth recurrence. Start with its [`README.md`](2026-10-02/README.md).
- [`2026-09-28/`](2026-09-28/) — J-Link BSOD recovery, transceiver
  firmware, nRF52833 bring-up, two-board link. Start with its
  [`README.md`](2026-09-28/README.md).

Convention: `docs/sessions/<YYYY-MM-DD>/` holds `README.md` (investigation
summary), an agent-named `<AGENT>_SESSION_LOG.md` (chronological record), and
`debug-evidence/` (raw artifacts). Existing MUSE-prefixed logs are historical;
Codex sessions use `CODEX_SESSION_LOG.md`. Records are append-only history.
