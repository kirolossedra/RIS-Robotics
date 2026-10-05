# Session 2026-09-28 — J-Link recovery, transceiver firmware, nRF52833 bring-up, two-board link

Date: 2026-09-28. Location: this folder (`docs/sessions/2026-09-28/`).
Full chronological record: [`MUSE_SESSION_LOG.md`](MUSE_SESSION_LOG.md).
Raw Windows/J-Link artifacts: [`debug-evidence/`](debug-evidence/).
Firmware validation evidence: `../firmware/validation/`.

## 1. Windows / J-Link BSOD investigation and stack reset

Two Windows bugcheck `0xA` crashes during J-Link operations were preserved
(`091626-15718-01.dmp`, `092826-15921-01.dmp` in `debug-evidence/`;
SEGGER drivers loaded, faulting instruction unattributed). The old
J-Link V9.22 installation was fully removed (uninstaller + Driver Store
`oem17/oem26/oem44` packages) and SEGGER J-Link V9.80 installed
(`C:\Program Files\SEGGER\JLink`, `JLinkARM.dll` 9.80), with a
known-good USB cable. Passive USB enumeration of probe S/N
`1050670813` (VID `1366`, PID `0101`) then passed, and J-Link Commander
opened the probe (`J-Link OB-nRF5340-NordicSemi`, HW V1.00, VTref
3.300 V), auto-updating its on-board firmware (2021 → June 2026).
Windows stayed stable from that point on. Report:
`debug-evidence/segger_jlink_reset_report.md`.

## 2. Controlled single-variable target tests (all PASS, all stable)

With the fresh stack, one new boundary per test, no retries:

- SWD connect to the target (then believed nRF52840): SW-DP
  `0x2BA01477`, APs enumerated, Cortex-M4 identified, exit 0.
- Chip erase of the application flash via J-Link: `Erasing done`,
  exit 0.

## 3. Transceiver firmware (single image, runtime roles)

Developed the shared nRF Connect SDK/Zephyr application
(`firmware/transceiver/`, NCS v3.2.3): one image, runtime TX/RX roles
(Button 2 / `sw1`), orthogonal LE 1M / Coded S=8 PHY switching
(Button 1 / `sw0`), latched `OBS`/`CLR` over UART, RX dedup, continuous
role LEDs + `led2` PHY indicator, boot TX + Coded S=8, requested-vs-active
role semantics (failed transport restores the previous side; dark LEDs if
both sides down). Pure protocol/role logic in `src/protocol.h` with a
host-side test (`tests/test_protocol.c`, cross-compile-checked only).
Series as in the session log: PHY switching → single-image runtime roles
(`ble-runtime-0004`) → requested/active correction → serial-contract
verification (RX `printk` proven routed to physical `uart0`).

## 4. Decision governance migration

`DL-001…DL-008` renamed to `<subsystem>-<environment>-<NNNN>-<name>.md`
(`ble-runtime-0001…0004`, `robot-runtime-0001/0002`, `robot-ros-0001`,
`robot-hardware-0001`), pair-local chronological numbering, headings as
`# Decision:` + `**ID:**` + `**Previous ID:**`, supersede banners on the
old records, convention documented in `docs/decisions/README.md`.

## 5. Flash failures → APPROTECT → heap fault → wrong-chip root cause

- First flash verified but LEDs stayed dark; a read-only debug attach
  auto-unsecured (mass erase), destroying the evidence.
- APPROTECT mechanism verified from NCS source: default
  `NRF_APPROTECT_USE_UICR` makes `SystemInit` lock SWD pre-main whenever
  UICR is erased. No Kconfig keeps nRF52 debug open; the dev answer is
  device UICR `0x10001208 = 0x5A` (verified by read-back). Production
  builds keep the locking default. A `west flash` (nrfutil default
  `ERASE_ALL`) was proven to wipe a pre-written UICR value — write UICR
  strictly after programming.
- With SWD held open, a T+0 serial capture caught the real fault:
  `***** BUS FAULT ***** Imprecise data bus error` in `sys_heap_init`
  end-marker writes (heap end ≈ `0x2003FFF8`), before `main()`.
  Identical failure on stock Zephyr Blinky exonerated application logic.
- FICR read: PART `0x52833`, RAM `0x80` (128 KB), FLASH `0x200`
  (512 KB) — the chip is an **nRF52833**, valid SRAM
  `0x20000000–0x2001FFFF`. Images built for `nrf52840dk` (256 KB RAM)
  overran SRAM. Debugger SRAM write/read proved RAM healthy in range and
  non-sticky past `0x2001FFFF`. Classification: invalid heap/linker
  configuration (wrong SoC target), Case B.

## 6. Corrected build, boot proof, two-board link (PASS)

- Rebuilt pristinely for `nrf52833dk/nrf52833` (exit 0, no warnings):
  FLASH 115916 B (22.11 % of 512 KB), RAM 21988 B (16.78 % of 128 KB);
  heap base `0x200055E8` size `0x1AA18` ends exactly `0x20020000`.
- Corrected flash order (recover → sector-erase program → UICR `0x5A`
  → verify → reset) on both boards (`1050670813`, `1050611489`; second
  board FICR-verified nRF52833 first). Clean boot banners, no faults;
  debugger backtrace proved `main()` → `bt_enable()` (returned) →
  `transceiver_run()` → `k_sleep`; GPIO showed LED init + `led2` ON
  (S=8); UART healthy and correctly silent in TX/`CLR`.
- Two-board smoke test PASS: TX=`COM14`, RX=`COM8`; `OBS`×3 → one
  `OBS`, `CLR`×3 → one `CLR`, `OBS`×3 → one `OBS`. Packet bytes:
  `13 16 116E…B47B 01 <00|01>` (UUID
  `7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11`, version `01`, state byte).

## 7. Open items at session end

Human LED-blink confirmation, Button 1/2 behavior on hardware,
coordinated over-air PHY-switch test, `rx_logger.py` JSONL run,
range/reliability, host-test execution (no host C compiler on the
machine), second-board long-run behavior. Human: visually confirm
the DK model marking for the record (FICR says nRF52833).
