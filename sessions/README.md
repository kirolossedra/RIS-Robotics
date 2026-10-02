# Sessions

## Authority boundary

Sessions are chronological engineering history and may contain debug scripts, logs, temporary test conditions, and observations. They are evidence, not current architecture authority.

Canonical current knowledge lives under [`../docs/`](../docs/). When a session changes architecture, feature maturity, a decision, or validation status, the corresponding canonical document must be updated separately.

## Session layout

One folder per engineering date, each self-contained: the session log,
a full investigation summary, and that date's debug evidence.

- [`2026-10-02/`](2026-10-02/) — Husky 1 bring-up and Joystick 3 Bluetooth recurrence. Start with its [`README.md`](2026-10-02/README.md).
- [`2026-09-28/`](2026-09-28/) — J-Link BSOD recovery, transceiver
  firmware, nRF52833 bring-up, two-board link. Start with its
  [`README.md`](2026-09-28/README.md).

Convention: `sessions/<YYYY-MM-DD>/` holds `README.md` (investigation
summary), `MUSE_SESSION_LOG.md` (chronological record), and
`debug-evidence/` (raw artifacts). Records are append-only history.
