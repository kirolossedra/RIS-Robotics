# Sessions

One folder per engineering date, each self-contained: the session log,
a full investigation summary, and that date's debug evidence.

- [`2026-09-28/`](2026-09-28/) — J-Link BSOD recovery, transceiver
  firmware, nRF52833 bring-up, two-board link. Start with its
  [`README.md`](2026-09-28/README.md).

Convention: `sessions/<YYYY-MM-DD>/` holds `README.md` (investigation
summary), `MUSE_SESSION_LOG.md` (chronological record), and
`debug-evidence/` (raw artifacts). Records are append-only history.
