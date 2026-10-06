# Firmware validation records

## Contents

- [Evidence ownership](#evidence-ownership)
- [Records](#records)
- [Reusable tooling](#reusable-tooling)
- [Conventions](#conventions)

Dated, board-level evidence for the RIS Transceiver firmware. Each record
states the procedure, the exact observed result, and what remains open —
so a commit carrying these files is self-describing.


## Evidence ownership

This directory is the raw evidence store for firmware/hardware validation, including executable smoke-test tooling. Canonical claims and maturity synthesis live in [`../../docs/validation/`](../../docs/validation/).

A stub-mode PASS validates the stub and the boundary exercised by it. It does not validate natural over-air reception unless that real path was part of the test.


## Records

- [`2026-09-28-single-board-bringup.md`](2026-09-28-single-board-bringup.md) —
  nRF52833 identification, corrected flash order (recover → sector-erase
  program → UICR `0x5A` → verify → reset), clean boot proof, running-app
  evidence (debugger backtrace, GPIO, UART).
- [`2026-09-28-two-board-smoke-test.md`](2026-09-28-two-board-smoke-test.md) —
  over-air TX → BLE → RX episode test (PASS), exact packet-byte layout,
  proven vs open items.
- [`2026-10-02-rx-stub-mode-test.md`](2026-10-02-rx-stub-mode-test.md) —
  RX Natural/Forced CLR/Forced OBS button and LED test; serial output and
  over-air suppression remain open.
- [`2026-10-05-event-driven-uart.md`](2026-10-05-event-driven-uart.md) —
  async UART build and two-board flash verification; physical RX serial
  transition capture remains pending.

## Reusable tooling

- [`smoke_test.py`](smoke_test.py) — two-board episode test:
  `python smoke_test.py --tx <TXPORT> --rx <RXPORT>`
  (needs `pyserial`; roles must already be set with Button 2; swap the
  ports and re-run if a run stays silent).
- [`../tools/rx_logger.py`](../tools/rx_logger.py) — timestamped JSON
  Lines logger for the RX console.

## Conventions

- Records are append-only history: correct by adding a new dated record,
  never by rewriting an old result.
- Anything requiring hardware states the exact board(s), probe serial(s),
  image, and date.
