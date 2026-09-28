# Validation: 2026-09-28 single-board bring-up (nRF52833 correction)

Date: 2026-09-28.
Board: nRF52833 DK (J-Link S/N `1050670813`; second board `1050611489`
later confirmed identical MCU via FICR).

## Background

Images built for `nrf52840dk/nrf52840` (256 KB RAM assumption) BusFaulted
before `main()` on this hardware: Zephyr POST_KERNEL libc malloc-arena
init writes heap metadata up to `0x2003FFF8`, but the physical chip is an
nRF52833 with 128 KB SRAM (`0x20000000–0x2001FFFF`). FICR evidence:
PART `0x52833`, RAM `0x80`, FLASH `0x200`. Direct debugger SRAM
write/read proved RAM healthy inside its range and non-sticky past
`0x2001FFFF`. Identical failure on stock Zephyr Blinky exonerated
application logic. Full evidence: `MUSE_SESSION_LOG.md`.

## Corrective procedure (works, reusable per board)

1. `nrfjprog --recover` (clean slate; also clears UICR).
2. `nrfjprog --program build/transceiver/merged.hex --sectorerase --verify`
   with the `nrf52833dk/nrf52833` image (sector erase preserves UICR).
3. `nrfjprog --memwr 0x10001208 --val 0x5A --verify` (dev-open
   APPROTECT; NCS default `NRF_APPROTECT_USE_UICR` otherwise locks SWD
   at every boot — production images keep the locking default).
4. Read back UICR (`0x0000005A`) and vectors (nrf52833 image values).
5. `nrfjprog --reset`; capture serial from T+0.

Two ordering traps, both hit during bring-up:

- `west flash` (nrfutil default `ERASE_ALL`) wipes a previously written
  UICR value → write UICR strictly AFTER programming.
- Windows COM numbers shift on every re-enumeration; always re-resolve
  the MI_00 CDC port (target `uart0`), never assume persistence.

## Observed result (PASS)

- Program + verify OK; UICR `0x5A` survived reset; SWD stays open.
- T+0 serial: clean Zephyr/NCS boot banner, no fault text.
- Debugger halt sample: PC in `arch_cpu_idle`/`idle` thread, no
  exception, fault registers zero; main-thread backtrace shows
  `main()` → `bt_enable()` (returned) → `transceiver_run()` → `k_sleep`.
- GPIO P0: DIR `0xE060` (LED P0.13/14/15 + UART as outputs — `leds_init`
  ran); OUT bit15 LOW = `led2` ON = Coded S=8 (`phy_indicator_update`
  ran); role-LED blink phase needs human eyes.
- UART opens at 115200, silent post-boot (correct for TX/`CLR`), writes
  accepted, no fault banner.

## Still open at the time

Human LED-blink confirmation, Button 1/2 behavior on hardware,
over-air tests with the second board (covered separately in
`2026-09-28-two-board-smoke-test.md` once both boards were up).
