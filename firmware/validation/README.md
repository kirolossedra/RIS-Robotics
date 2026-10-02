# Firmware validation records

Dated, board-level evidence for the RIS Transceiver firmware. Each record
states the procedure, the exact observed result, and what remains open —
so a commit carrying these files is self-describing.

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
