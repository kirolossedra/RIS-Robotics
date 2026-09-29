# J-Link USB Transport / Host-Interface Instability Causing Windows BSODs

> Likely unstable USB/J-Link host communication, with the original USB cable as the strongest observed trigger. The J-Link host installation and probe firmware were also refreshed during the investigation, so exact single-factor causality was not isolated. The nRF52840 application firmware was ruled out as the primary cause.

## 2026-09-28 — Session initialization and operating authority established

### User request

Establish persistent autonomous engineering session with broad workspace authority, evidence-driven workflow, and per-prompt logging to `MUSE_SESSION_LOG.md`.

### Actions performed

- Inspected workspace root `P:\Github\RIS-Robotics`.
- Read `README.md` to confirm project architecture and existing docs structure.
- Checked `MUSE_SESSION_LOG.md` — did not exist.
- Ran `git status --short --branch`, `git log --oneline -5`, `git diff --stat` for baseline.
- Created `MUSE_SESSION_LOG.md`.

### Results

- Workspace root contains: `.git/`, `build/`, `decision-logs/`, `firmware/`, `system/`, `tools/`, plus untracked SEGGER/JLink diagnostics and two `.dmp` files.
- Branch state: `main...origin/main [behind 19]`, no staged/modified tracked files.
- Untracked files: `091626-15718-01.dmp`, `092826-15921-01.dmp`, `JLink_Windows_x86_64.exe`, `jlink_passive_enumeration.json`, `jlink_probe_open_test.jlink`, `segger_cleanup_log.txt`, `segger_install_log.txt`, `segger_inventory_before.json`, `segger_jlink_reset_report.md`, `tools/`.
- Latest commit: `e3f6aad firmware-not-tested`.
- README confirms architecture: Radar/RIS detection → serial → BLE Coded PHY S=8 → Jackal-side laptop → SSH/Ethernet → Jackal ROS STOP-over-joystick arbitration.

### Changes made

- Created `MUSE_SESSION_LOG.md` (this file). No other persistent changes.

### Conclusion

Session operating rules accepted. Workspace baseline recorded. No engineering task yet requested.

### Next boundary

Awaiting first substantive user prompt.

## 2026-09-28 — Fetch and pull, verify no conflicts

### User request

Fetch/pull remote and ensure there are no conflicts.

### Actions performed

- Ran `git fetch origin`.
- Ran `git rev-list --left-right --count HEAD...origin/main` (result: 0 ahead, 19 behind — fast-forward safe).
- Ran `git pull --ff-only origin main`.
- Verified with `git status --short --branch`, `git rev-list --left-right --count HEAD...origin/main`, `git diff --stat`, `git ls-files -u`.

### Results

- Fetch succeeded.
- Pull succeeded with exit code 0, fast-forward `e3f6aad..5e7ea35`, 16 files changed (+1031/-92).
- Post-pull state: `main...origin/main`, 0 ahead / 0 behind, in sync.
- `git diff --stat`: empty (no modified tracked files).
- `git ls-files -u`: empty (no unmerged/conflicted paths).
- Only untracked files remain: two `.dmp` files, SEGGER/JLink logs/reports, `JLink_Windows_x86_64.exe`, `tools/`, and `MUSE_SESSION_LOG.md`.

### Changes made

- Updated tracked working tree via fast-forward pull to `5e7ea35 docs: record dual-robot architecture and Sep 17 session`.
- Appended this entry to `MUSE_SESSION_LOG.md`. No other persistent changes.

### Conclusion

Repository is up to date with `origin/main` and conflict-free.

### Next boundary

Work tree contains untracked diagnostic/tool artifacts that are not yet ignored or committed; disposition (ignore, remove, or commit) is unresolved if cleanup is desired.

## 2026-09-28 — Controlled J-Link SWD target-connection test (one new boundary)

### User request

Investigate Windows/J-Link crash with Nordic board. Prior established evidence: bugcheck 0xA history, clean J-Link V9.80 install, new USB cable, passive enumeration PASS, probe-open PASS with on-board firmware updated 2021 → June 2026, no target connection yet tested, no crashes since stack reset. Goal: test exactly one new boundary — can the probe establish SWD to the target MCU without crashing Windows. No erase/recovery/flash/memory-write. Run once, capture output and exit code, then report and log.

### Actions performed

- Read `MUSE_SESSION_LOG.md` (2 prior entries), workspace root, `segger_jlink_reset_report.md`, `jlink_passive_enumeration.json`, `jlink_probe_open_test.jlink`, `segger_cleanup_log.txt`, `segger_install_log.txt`, `firmware/README.md`, `firmware/transceiver/CMakeLists.txt`, `firmware/transceiver/prj.conf`, `build/transceiver-tx/build_info.yml`, `build/transceiver-tx/zephyr_settings.txt`, `build/transceiver-tx/CMakeCache.txt`.
- Verified J-Link install: `C:\Program Files\SEGGER\JLink\JLinkARM.dll` file/product version 9.80 (matches established evidence).
- Determined exact SEGGER device identifier from local evidence (see Results).
- NOTE — extra probe activity before the controlled test: during install verification I invoked `JLink.exe -CommanderScript jlink_probe_open_test.jlink` (existing probe-open script: DisableAutoUpdateFW / USB / ShowFWInfo / ShowHWStatus / Exit). It printed the V9.80 banner and `J-Link Command File read successfully`. This was a repeat of the already-passing probe-open step, not the firmware-update test, and performed no target operation. Disclosed here because the prompt asked not to repeat completed tests.
- Created single-use commander script at `C:\Users\Ordinateur de Kiro\AppData\Local\Temp\opencode\jlink_swd_connect_test.jlink` with exactly:
  - `USB 1050670813`, `Device nRF52840_xxAA`, `IF SWD`, `Speed 1000`, `Connect`, `Exit`.
- Ran it EXACTLY ONCE: `& "C:\Program Files\SEGGER\JLink\JLink.exe" -CommanderScript <script>`. Captured full console output and `JLINK_EXIT:0`.
- Verified Windows stability after the test: `Win32_OperatingSystem.LastBootUpTime`, `C:\Windows\Minidump\*.dmp`, workspace `*.dmp`. No retry, no speed change, no recovery/erase/flash, no IDE/nRF Util/west involvement.

### Results

Target identification (direct local evidence, no guessing from probe name):

- `firmware/README.md:7-8`: verified build target is Nordic nRF52840 DK, board target `nrf52840dk/nrf52840`.
- `build/transceiver-tx/build_info.yml`: board name `nrf52840dk`, qualifiers `nrf52840`, DTS `nrf52840dk_nrf52840.dts`, SVD `nrf52840.svd`.
- `build/transceiver-tx/CMakeCache.txt`: `BOARD=nrf52840dk/nrf52840`, `SOC_SVD_FILE=.../nrf52840.svd`.
- Exact Nordic MCU: nRF52840.
- Exact SEGGER J-Link device identifier selected: `nRF52840_xxAA` — the unique `nRF52840*` match in JLinkARM.dll V9.80 ASCII strings; consistent with the nRF52840 target above.

SWD connection result: PASS.

J-Link output (single attempt, complete relevant console text):

```text
SEGGER J-Link Commander V9.80 (Compiled Sep 23 2026 13:21:17)
DLL version V9.80, compiled Sep 23 2026 13:20:16
J-Link Command File read successfully.
Processing script file...
J-Link>USB 1050670813
Connecting to J-Link ...O.K.
Firmware: J-Link OB-nRF5340-NordicSemi compiled Jun 11 2026 13:12:28
Hardware version: V1.00
J-Link uptime (since boot): 0d 00h 11m 23s
S/N: 1050670813
License(s): RDI,FlashBP,FlashDL,JFlash,GDB
USB speed mode: Full speed (12 MBit/s)
VTref=3.300V
J-Link>Device nRF52840_xxAA
J-Link>IF SWD
Selecting SWD as current target interface.
J-Link>Speed 1000
Selecting 1000 kHz as target interface speed
J-Link>Connect
Device "NRF52840_XXAA" selected.
Connecting to target via SWD
InitTarget() start
InitTarget() end - Took 4.95ms
Found SW-DP with ID 0x2BA01477
DPIDR: 0x2BA01477
CoreSight SoC-400 or earlier
Scanning AP map to find all available APs
AP[2]: Stopped AP scan as end of AP map has been reached
AP[0]: AHB-AP (IDR: 0x24770011, ADDR: 0x00000000)
AP[1]: JTAG-AP (IDR: 0x02880000, ADDR: 0x01000000)
Iterating through AP map to find AHB-AP to use
AP[0]: Core found
AP[0]: AHB-AP ROM base: 0xE00FF000
CPUID register: 0x410FC241. Implementer code: 0x41 (ARM)
Found Cortex-M4 r0p1, Little endian.
FPUnit: 6 code (BP) slots and 2 literal slots
CoreSight components:
ROMTbl[0] @ E00FF000
[0][0]: E000E000 CID B105E00D PID 000BB00C SCS-M7
[0][1]: E0001000 CID B105E00D PID 003BB002 DWT
[0][2]: E0002000 CID B105E00D PID 002BB003 FPB
[0][3]: E0000000 CID B105E00D PID 003BB001 ITM
[0][4]: E0040000 CID B105900D PID 000BB9A1 TPIU
[0][5]: E0041000 CID B105900D PID 000BB925 ETM
Memory zones:
  Zone: "Default" Description: Default access mode
Cortex-M4 identified.
J-Link>Exit
Script processing completed.
JLINK_EXIT:0
```

Target information:

- Target voltage (VTref): 3.300 V.
- SW-DP / DPIDR: `0x2BA01477` (SW-DP found).
- CPU/core: Cortex-M4 r0p1, little endian; CPUID `0x410FC241`, implementer `0x41` (ARM); FPU unit 6 code + 2 literal slots; ROM base `0xE00FF000` with SCS-M7/DWT/FPB/ITM/TPIU/ETM components enumerated.
- Access ports: AP[0] AHB-AP (IDR `0x24770011`) — core found; AP[1] JTAG-AP (IDR `0x02880000`); AP[2] end of map.
- Target protection/security state: no lock/APPROTECT error or warning reported; connection and AP scan completed normally.
- J-Link warnings: none in captured output.

Windows stability: Windows remained stable throughout the operation. J-Link exited normally (exit code 0), the session continued, LastBootUpTime `2026-09-28 10:40:36` (pre-test boot, no reboot), and no new dump appeared — `C:\Windows\Minidump` and workspace contain only the two preserved dumps (`091626-15718-01.dmp`, `092826-15921-01.dmp`).

Target modification: None. No erase, recovery, flash, HEX/BIN/ELF load, memory write, `nrfjprog --eraseall/--recover`, reset/halt beyond J-Link's normal `Connect`/`InitTarget()` sequence, or IDE/debugger involvement.

### Changes made

- Created temp commander script `C:\Users\Ordinateur de Kiro\AppData\Local\Temp\opencode\jlink_swd_connect_test.jlink` (outside workspace; one-use artifact for this test).
- Appended this entry to `MUSE_SESSION_LOG.md`. No workspace source files modified. No Git commits, no pushes. No target flash/erase/recovery.

### Conclusion

- PC → USB → J-Link path: working (probe opened, S/N 1050670813, V9.80, VTref 3.3 V, stable).
- J-Link → target SWD path: working — SW-DP detected, APs enumerated, Cortex-M4 identified at 1000 kHz with device `nRF52840_xxAA`.
- Target access blocked/protected: no evidence of blocking; access succeeded.
- This experiment establishes only that a basic SWD connect is stable in the current stack/cable state. It says nothing about erase/flash/debug stability, which remain untested per the one-variable constraint.

### Next boundary

Erase, recovery, flashing, and application-firmware load/debug remain deliberately untested. Do not proceed to them without an explicit new prompt.

## 2026-09-28 — Controlled J-Link nRF52840 erase test (one new boundary)

### User request

Using established evidence (passive enumeration PASS, probe-open PASS, firmware update done, SWD connect PASS to nRF52840 at 1000 kHz, Windows stable), perform exactly ONE new operation with J-Link Commander V9.80: erase the application flash of the connected nRF52840. No replacement firmware afterward. One J-Link session (`USB / Device / IF SWD / Speed 1000 / Connect / Erase / Exit`), run once, no retry/recover/speed-change/flash/nRF Util/west/IDE/memory-write, then report and log.

### Actions performed

- Read `MUSE_SESSION_LOG.md` (3 prior entries) and reused verified target parameters: MCU nRF52840, SEGGER device `nRF52840_xxAA`, probe S/N `1050670813`, SWD 1000 kHz.
- Created single-use script `C:\Users\Ordinateur de Kiro\AppData\Local\Temp\opencode\jlink_erase_test.jlink` with exactly `USB 1050670813`, `Device nRF52840_xxAA`, `IF SWD`, `Speed 1000`, `Connect`, `Erase`, `Exit`.
- Ran it EXACTLY ONCE via `JLink.exe -CommanderScript`. Captured full output and `JLINK_EXIT:0`.
- Verified stability: `LastBootUpTime`, `C:\Windows\Minidump\*.dmp`, workspace `*.dmp`. Stopped after success; no verification tool, no further operation.

### Results

Erase result: PASS.

J-Link output (single session, diagnostically relevant text):

```text
SEGGER J-Link Commander V9.80 (Compiled Sep 23 2026 13:21:17)
DLL version V9.80, compiled Sep 23 2026 13:20:16
J-Link Command File read successfully.
Processing script file...
J-Link>USB 1050670813
Connecting to J-Link ...O.K.
Firmware: J-Link OB-nRF5340-NordicSemi compiled Jun 11 2026 13:12:28
Hardware version: V1.00
J-Link uptime (since boot): 0d 00h 16m 15s
S/N: 1050670813
License(s): RDI,FlashBP,FlashDL,JFlash,GDB
USB speed mode: Full speed (12 MBit/s)
VTref=3.300V
J-Link>Device nRF52840_xxAA
J-Link>IF SWD
Selecting SWD as current target interface.
J-Link>Speed 1000
Selecting 1000 kHz as target interface speed
J-Link>Connect
Device "NRF52840_XXAA" selected.
Connecting to target via SWD
InitTarget() start
InitTarget() end - Took 4.35ms
Found SW-DP with ID 0x2BA01477
DPIDR: 0x2BA01477
CoreSight SoC-400 or earlier
Scanning AP map to find all available APs
AP[2]: Stopped AP scan as end of AP map has been reached
AP[0]: AHB-AP (IDR: 0x24770011, ADDR: 0x00000000)
AP[1]: JTAG-AP (IDR: 0x02880000, ADDR: 0x01000000)
Iterating through AP map to find AHB-AP to use
AP[0]: Core found
AP[0]: AHB-AP ROM base: 0xE00FF000
CPUID register: 0x410FC241. Implementer code: 0x41 (ARM)
Found Cortex-M4 r0p1, Little endian.
FPUnit: 6 code (BP) slots and 2 literal slots
CoreSight components:
ROMTbl[0] @ E00FF000
[0][0]: E000E000 CID B105E00D PID 000BB00C SCS-M7
[0][1]: E0001000 CID B105E00D PID 003BB002 DWT
[0][2]: E0002000 CID B105E00D PID 002BB003 FPB
[0][3]: E0000000 CID B105E00D PID 003BB001 ITM
[0][4]: E0040000 CID B105900D PID 000BB9A1 TPIU
[0][5]: E0041000 CID B105900D PID 000BB925 ETM
Memory zones:
  Zone: "Default" Description: Default access mode
Cortex-M4 identified.
J-Link>Erase
No address range specified, 'Erase Chip' will be executed
'erase': Performing implicit reset & halt of MCU.
Reset type: NORMAL (https://kb.segger.com/J-Link_Reset_Strategies)
Reset: Halt core after reset via DEMCR.VC_CORERESET.
Reset: Reset device via AIRCR.SYSRESETREQ.
Erasing device...
J-Link: Flash download: Only internal flash banks will be erased.
To enable erasing of other flash banks like QSPI or CFI, it needs to be enabled via "exec EnableEraseAllFlashBanks"
J-Link: Flash download: Total time needed: 0.843s (Prepare: 0.368s, Compare: 0.000s, Erase: 0.229s, Program: 0.000s, Verify: 0.000s, Restore: 0.244s)
Erasing done.
J-Link>Exit
Script processing completed.
JLINK_EXIT:0
```

Target confirmation:

- nRF52840 / `nRF52840_xxAA` / SWD 1000 kHz / probe S/N `1050670813` / VTref 3.300 V.

Erase detail:

- Erase started: yes (`Erase Chip`, implicit reset & halt, NORMAL reset via DEMCR.VC_CORERESET + AIRCR.SYSRESETREQ).
- Erase completed: yes (`Erasing done.`).
- Reported duration: total 0.843 s (Prepare 0.368 s, Compare 0.000 s, Erase 0.229 s, Program 0.000 s, Verify 0.000 s, Restore 0.244 s); internal flash banks only.
- Warnings/errors: none; informational note only about QSPI/CFI banks requiring `EnableEraseAllFlashBanks` (not used).
- Process exit code: 0.

Windows stability: Windows remained stable throughout. No freeze/BSOD, normal J-Link exit, session continued, LastBootUpTime `2026-09-28 10:40:36` (pre-test boot, no reboot), no new dump — minidump dir and workspace contain only the two preserved dumps.

Additional target operations: no recovery occurred, no firmware was flashed, no HEX/BIN/ELF image was loaded, no arbitrary memory write, no `nrfjprog`/nRF Util/`west flash`/IDE/OpenOCD involvement. J-Link's own `Erase` flow (reset/halt + internal-flash erase + restore) is the only target modification.

### Changes made

- Created temp script `C:\Users\Ordinateur de Kiro\AppData\Local\Temp\opencode\jlink_erase_test.jlink` (outside workspace).
- Target nRF52840 application flash erased (chip erase of internal flash banks via J-Link).
- Appended this entry to `MUSE_SESSION_LOG.md`. No workspace source files modified. No Git commits or pushes.

### Conclusion

- Basic J-Link communication is stable.
- SWD target connection is stable.
- nRF52840 erase is stable in this configuration.
- No attribution is made about which earlier change (cable, host J-Link install, probe firmware) resolved the original BSOD, since all changed during the investigation.

### Next boundary

Flashing replacement firmware remains deliberately untested. Do not proceed to flashing without an explicit new prompt.

## 2026-09-28 — Transceiver firmware: LE 1M + Coded S=8, button PHY switching, build-only

### User request

Develop the BLE transceiver firmware and build successfully (CODE DEVELOPMENT AND BUILD ONLY, no flash). One board connected (left erased), second board absent: no hardware deployment or two-board test. Preserve shared codebase; no runtime TX↔RX role switching by button; keep compile-time roles unless documented otherwise. Required: LE 1M + Coded S=8 with button PHY switching, TX latched OBS/CLR, RX dedup, LED role indication, minimal protocol, reliability review, build both roles for nrf52840dk/nrf52840, docs, no hardware interaction, git status, session log.

### Actions performed

- Read `MUSE_SESSION_LOG.md` (title + 4 entries, J-Link record preserved), `firmware/README.md`, `firmware/transceiver/src/main.c`, `Kconfig`, `prj.conf`, `tx.conf`, `rx.conf`, `build/transceiver-tx` metadata, `system/system.md` + `control-signal-path.md` (transceiver sections), `decision-logs/DL-004` (full), DL index.
- Grepped firmware/system/decision-logs for button/PHY/switching evidence.
- Created `firmware/transceiver/src/protocol.h`, rewrote `firmware/transceiver/src/main.c`, created `firmware/transceiver/tests/test_protocol.c`.
- Updated `firmware/README.md`, created `decision-logs/DL-007-transceiver-phy-modes-button-switching.md`, added DL-007 row to `decision-logs/README.md`.
- Built TX and RX pristine with NCS v3.2.3 west (workspace-less `-z`, quoted `-DEXTRA_CONF_FILE`), verified `.config`, artifacts, role-specific binary strings; cross-compiled host test to object with `-Wall -Wextra`.
- `git status` / `git diff --stat`. No flash/erase/recovery/debug commands run; J-Link/nRF tools never invoked.

### Results

Existing architecture found (repo truth):

- Layout: one app (`CMakeLists.txt`, `Kconfig` role choice TX/RX + blink interval, `prj.conf`, `tx.conf`/`rx.conf` fragments, `src/main.c`); role selection is compile-time via `EXTRA_CONF_FILE` (DL-004). No second implementation exists.
- BLE transport: connectionless non-connectable extended advertising (TX) + passive scanning (RX); 128-bit Service Data UUID `7bb4f91d-...`, version byte 0x01, state byte 0x00/0x01. No GATT/connections.
- UART: TX `uart_poll_in` newline-delimited exact `OBS`/`CLR` (else ignored); RX `printk` `OBS`/`CLR`.
- Button behavior: NONE existed — no button code, no sw0/dk_btn references, no button docs anywhere. Accepted design (DL-004) was coded-S=8-only. The prompt's "established button behavior" was therefore treated as a requirement to implement (button→PHY switching), not as existing code; the forbidden behavior (button→role switching) was not introduced.
- LED: TX toggles led0+led1, RX led0, 500 ms (aliases, not pin numbers).
- PHY: TX ext-adv CODED+REQUIRE_S8+CODING_SELECTION; RX scan CODED|NO_1M. No 1M, no switching.

Changes made (why):

- `src/protocol.h` (new): dependency-free `tx_parse_command` (exact OBS/CLR else IGNORE incl. NULL) and `rx_dedup_update` (first-OBS emits, repeats silent, first-CLR-after-OBS emits, startup CLR silent, malformed bytes silent+stateless, NULL-guard); shared by firmware and host test, no behavior change.
- `src/main.c` (rewritten, working behavior preserved): uses protocol.h; adds `enum transceiver_phy` (default CODED_S8), Button-1 `sw0` ISR (200 ms debounce, atomic flag polled in loops), static-const adv params per mode + `tx_ble_restart` (state-preserving, fallback to previous PHY, rare `ERR adv-restart` printk), `rx_scan_options` + `rx_ble_restart` with dedup-epoch reset + `ERR scan-restart` printk, optional-free `led2` PHY indicator (on=S=8/off=1M) via `phy_indicator_update`; TX overflow/invalid handling identical semantics with explicit comments; `sw0`/`led2` aliases required with `#error` like existing LED checks.
- `tests/test_protocol.c` (new): assert-based host test (TX parse incl. case/padding/overlong/NULL; RX dedup table, malformed bytes, startup-CLR, README episode sequence OBS×4 CLR×3 OBS×2 → OBS/CLR/OBS, NULL guard).
- `firmware/README.md`: board requirements (+sw0/led2), PHY-mode table + S=8 enforcement, button switching, LED indication, layout, smoke test marked not-performed, new Validation-status section (exact builds, env notes incl. `-z` and arg quoting, artifact paths, .config checks, test-compile note, BUILD ONLY/NO FLASH, remaining two-board work).
- `decision-logs/DL-007-*.md` (new) + index row: PHY modes + button switching decision, partial supersede of DL-004 coded-only, rationale, consequences. DL-004 itself untouched.

TX behavior: boot advertises CLEAR (S=8); exact OBS/CLR lines latch state and update adv only on change; invalid/overlong input ignored; Button 1 recreates advertiser on the other PHY with preserved state (fallback + ERR line on failure); LEDs led0+led1 blink, led2 = PHY.

RX behavior: boot unknown/silent; validated UUID/version/state bytes feed `rx_dedup_update`; emits first OBS then first CLR per episode, suppresses repeats and startup CLR, ignores malformed bytes without state change; Button 1 restarts scan on the other PHY and resets epoch to unknown; led0 blinks, led2 = PHY.

BLE PHY behavior: 1M = ext-adv without coded options / scan options 0 (1M only); Coded = ext-adv CODED+REQUIRE_S8_CODING+CODING_SELECTION / scan CODED|NO_1M; S=8 enforced via SDK v2 coding-selection API, no S=2 path; switching = Button-1 edge → ISR flag → loop teardown/recreate (TX) or scan stop/start (RX).

Builds (both `nrf52840dk/nrf52840`, NCS v3.2.3, pristine, exit 0, zero warnings):

- TX: `west -z C:/ncs/v3.2.3/zephyr build -p always -b nrf52840dk/nrf52840 firmware/transceiver -d build/transceiver-tx -- "-DEXTRA_CONF_FILE=tx.conf"` → `build/transceiver-tx/transceiver/zephyr/zephyr.hex` (285887 B), `.elf`, `merged.hex`; FLASH 101608 B (9.69 %), RAM 23128 B (8.82 %); `.config`: ROLE_TX, BROADCASTER, CODING_SELECTION, PHY_CODED, GPIO, BT.
- RX: same with `rx.conf` → `build/transceiver-rx/...` hex (302426 B), `.elf`, `merged.hex`; `.config`: ROLE_RX, OBSERVER, BROADCASTER unset, same radio/GPIO/BT.
- Environment notes: `ZEPHYR_BASE`, `ZEPHYR_TOOLCHAIN_VARIANT=zephyr`, `ZEPHYR_SDK_INSTALL_DIR`, toolchain `opt/bin`+`mingw64/bin` on PATH; cross-drive west needs `-z` from repo cwd; `-DEXTRA_CONF_FILE` value must be quoted (unquoted `tx.conf` split into `tx` + `.conf` by the shell layer, failing Kconfig).

Tests/checks: TX+RX pristine builds pass warning-free; `.config` asserts role/radio/UART-enabling options; ELF string check proves role separation (TX has `adv-restart` not `scan-restart` and vice versa, both carry OBS/CLR); `test_protocol.c` compiles warning-free (`-Wall -Wextra`, ARM object, exit 0) but could not be executed — no host C compiler on this machine (no MSVC/clang/gcc; only ARM cross gcc); episode/dedup vectors verified by inspection against protocol.h. Two intermediate west failures (cross-drive relpath; arg splitting) were environment issues, diagnosed and resolved, not code defects.

Hardware interaction: No hardware flashing, erase, recovery, debug connection, or target modification was performed. J-Link/`nrfjprog`/nRF Util/`west flash`/IDE never invoked; `west build` only compiles. Attached nRF52840 left erased; second board absent.

Remaining physical validation (needs 2nd nRF52840 DK): TX↔RX packet exchange, OBS/CLR propagation, duplicate suppression over air, Button-1 switching on both devices, Coded S=8 over the real radio link, UART host integration both sides, on-hardware LED behavior, range/reliability characterization. Host-test execution pending a machine with a host C compiler.

### Changes made

- Modified: `firmware/transceiver/src/main.c`, `firmware/README.md`, `decision-logs/README.md`.
- Created: `firmware/transceiver/src/protocol.h`, `firmware/transceiver/tests/test_protocol.c`, `decision-logs/DL-007-transceiver-phy-modes-button-switching.md`.
- Rebuilt (gitignored): `build/transceiver-tx/`, `build/transceiver-rx/` (+ shared `build/.zephyr-cache` reuse).
- Temp artifacts (outside workspace): `tx_build1.log`, `tx_build2.log`, `rx_build.log`, `test_protocol.o` under `...\Temp\opencode\`.
- Appended this entry to `MUSE_SESSION_LOG.md`. No commits, no pushes. All pre-existing untracked files (dumps, SEGGER logs, tools/) preserved; tracked tree otherwise untouched.

### Conclusion

- Both transceiver roles compile warning-free for `nrf52840dk/nrf52840` with LE 1M + explicit Coded S=8, button PHY switching, preserved protocol/LED/role semantics, and documented reliability behavior.
- Only non-hardware validation is complete; all over-the-air and on-hardware behavior is explicitly unproven until the second board is connected.
- No claim about which earlier change fixed the original BSOD (cable, host install, probe firmware all changed).

### Next boundary

Flash TX/RX images and run the two-board OBS→CLR smoke test only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Serial interface contract verification (no code change)

### User request

Before flashing, verify from code and Zephyr configuration that TX receives OBS/CLR from the physical UART and RX emits accepted OBS/CLR transitions to the physical UART the Jackal computer can read. Determine exactly where printk is routed in both builds (prj.conf, tx/rx.conf, chosen console, generated .config, UART/console aliases). If RX printk is guaranteed to reach the physical UART, make no code change and show evidence; otherwise switch RX control output to an explicit UART path (printk may stay for debug). Preserve dedup/BLE/PHY-switch/LEDs/TX behavior. Rebuild warning-free if changed; no flash; no J-Link. Report TX input, RX output, console routing, changes, builds; append to log.

### Actions performed

- Inspected `firmware/transceiver/prj.conf`, `tx.conf`, `rx.conf`, `src/main.c` console binding, board DTS (`nrf52840dk_nrf52840.dts`, `-pinctrl.dtsi`), and both builds' generated `.config` + `zephyr.dts`.
- Grepped both `.config` files for PRINTK/CONSOLE/UART_CONSOLE/STDOUT_CONSOLE/RTT/SHELL/LOG/BT-debug/UART options; extracted `chosen { zephyr,console }`, uart0 status/speed/pinctrl from generated and board devicetree.
- Ran no-op `ninja -C build/transceiver-tx` and `build/transceiver-rx` to confirm both images are current (build-only, no hardware).
- Made no source or configuration change. No flash/erase/recovery/debug; J-Link never invoked.

### Results

Verdict: RX `printk("OBS")` / `printk("CLR")` is guaranteed to reach the physical UART by explicit configuration. No code change made.

TX serial input (exact path/framing):

- `main.c`: `console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console))`; TX loop calls `uart_poll_in(console, &byte)`; newline (`\r`/`\n`) frames lines into `line[8]`; `tx_parse_command` accepts only exact `OBS`/`CLR`.
- `zephyr,console = &uart0` (board DTS + both generated `zephyr.dts`); uart0 `nordic,nrf-uarte`, `status okay`, `current-speed 115200` (8N1 default, no parity), pinctrl RX P0.8 (+CTS P0.7). P0.6/P0.8 are the DK's documented VCOM pins to the on-board interface MCU USB-CDC port — the physical serial port the sensing PC opens.

RX serial output (exact path/framing):

- Accepted transitions call `printk("OBS\n")` / `printk("CLR\n")` after `rx_dedup_update`; bytes are plain ASCII with `\n` framing, matching the logger's line reader and the documented `OBS\n`/`CLR\n` protocol.

Console routing (why it is guaranteed, not implicit):

- `prj.conf` explicitly selects `CONFIG_SERIAL`, `CONFIG_CONSOLE`, `CONFIG_UART_CONSOLE` (plus `CONFIG_BT` stack options) — the UART-console backend is a deliberate project selection, not a default accident.
- Generated `.config`, identical in both roles: `CONFIG_PRINTK=y`, `CONFIG_CONSOLE=y`, `CONFIG_UART_CONSOLE=y`, `CONFIG_STDOUT_CONSOLE=y`, `CONFIG_SERIAL=y`, `CONFIG_UART_NRFX=y`; `# CONFIG_USE_SEGGER_RTT is not set`, `# CONFIG_SHELL is not set`, `# CONFIG_LOG is not set`, `# CONFIG_UART_ASYNC_API is not set`. Nothing diverts printk (no RTT/semihosting/console-subsys) and nothing else writes to the console (no shell, no logging, no BT debug).
- Both generated `zephyr.dts` files: `zephyr,console = &uart0`, uart0 okay/115200/pinctrl as above; `main.c` binds the same chosen-console device for TX `uart_poll_in`. TX input and printk output therefore share the identical physical uart0.
- Rewriting RX output as manual `uart_poll_out` would emit identical bytes on identical pins through the identical driver — no additional guarantee, only duplicated code. Per the do-not-modify-unnecessarily instruction, RX keeps `printk` for the control lines.
- Known constraints (already documented in `firmware/README.md`): the only other console lines the firmware can emit are rare `ERR adv-restart` / `ERR scan-restart <err>` transport-failure diagnostics; hosts must ignore non-`OBS`/`CLR` lines. printk here is synchronous/polling; scan callback runs in thread context, not ISR.

### Changes made

- None. No source, Kconfig, conf, or devicetree modification was required. Appended this entry to `MUSE_SESSION_LOG.md` only.

### Conclusion

- End-to-end serial contract holds in the current images: sensing-PC USB-CDC → TX uart0 (`uart_poll_in`, exact OBS/CLR) → BLE → RX dedup → RX uart0 (`printk`, `OBS\n`/`CLR\n`) → Jackal-computer USB-CDC, all at 115200 8N1 through explicitly selected UART-console configuration.
- The machine-readable RX output path is explicit and stable (selected backend + fixed board console + fixed VCOM pins), not an implicit debug-console dependency.

### Next boundary

Flash TX/RX images and run the two-board OBS→CLR smoke test only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Single-image runtime TX/RX roles (DL-008), system-design propagation, one build

### User request

Architectural correction: compile-time TX/RX selection is NOT intended. ONE firmware image must run as TX or RX with runtime role switching via physical button — a system-design property reflected across firmware, system docs, decision logs, diagrams, build and test docs. Required: explicit runtime role state machine with Button 2 (sw1) role toggle + Button 1 (sw0) PHY toggle preserved, continuous LED role + PHY indication, boot TX+S=8, no NVS, TX→RX/RX→TX teardown paths, UART follows role (flush stale input, RX never consumes serial), PHY orthogonal to role, protocol unchanged, remove tx.conf/rx.conf/Kconfig roles, extend host tests (transitions, boundaries, 4 combos), ONE pristine build with config inspection, NO flashing/hardware, full file-path report incl. mandatory system-design table, contradiction re-grep, git status, session log.

### Actions performed

- Read `MUSE_SESSION_LOG.md` (title + prior entries; J-Link record preserved), current `main.c`/`protocol.h`/`Kconfig`/`prj.conf`, `firmware/README.md`, `system/system.md` (full), `system/control-signal-path.md` (full), root `README.md`, `session-logs/2026-09-17.md`, `robotics/README.md`, `rx_logger.py`, DL-004 (full), DL-007, DL index.
- Verified nRF52840 DK devicetree aliases: `sw0=&button0` (Button 1), `sw1=&button1` (Button 2), `led0/1/2` present (`nrf52840dk_nrf52840.dts:130-136`).
- Established repo truth: NO button→role mechanism existed; DL-004 encoded build-time roles + coded-only PHY; DL-007 added Button-1 PHY switching on build-time roles.
- Firmware: extended `protocol.h` with `tr_role`/`tr_phy`/`tr_mode` + toggle/press helpers + `TR_BOOT_*` defaults; rewrote `main.c` as single-image runtime machine; simplified `Kconfig` (blink interval only); added broadcaster+observer to `prj.conf`; deleted `tx.conf`/`rx.conf`; extended `tests/test_protocol.c` (boot defaults, role toggling, PHY/role independence over all 4 combos).
- Built ONE pristine image (`build/transceiver`), verified `.config`/artifacts/memory/binary strings; cross-compiled host test warning-free; removed stale gitignored `build/transceiver-tx|rx` dirs.
- Docs: rewrote `firmware/README.md` role/build/validation sections; updated `system/system.md` (mermaid labels, §1 transceiver paragraph, LED sentence, status table); updated `system/control-signal-path.md` (route diagram, §4 hardware+function, §5 diagram, §8 node, §9 table); updated root `README.md` (chain, firmware bullet); marked DL-004/DL-007 Superseded with traceability banners (bodies intact); created DL-008; updated DL index.
- Re-grepped for compile-time/two-image/role-flash contradictions; `git status`/`git diff --stat`. No flash/erase/recovery/debug; J-Link/nRF tools never invoked.

### Results

Runtime architecture: `mode {role, phy}`; boot TX+S=8; Button 1 (sw0) toggles PHY preserving role; Button 2 (sw1) toggles role preserving PHY; TX blinks led0+led1, RX led0, led2 on=S=8/off=1M; TX→RX = stop adv/delete, drop UART partial, dedup=unknown, scan on current PHY, led1 off; RX→TX = stop scan, clear RX transient, latch=CLEAR, UART flush, advertise CLEAR on current PHY; start failures stay in requested role with rare ERR lines; no reboot/NVS/reflash.

Firmware changes: `src/main.c` rewritten (unified loop, transport start/stop per side, role/PHY ISRs with 200 ms debounce, UART consumed only in TX); `src/protocol.h` extended (role/PHY machine, boot defaults); `Kconfig` role choice removed; `prj.conf` +BROADCASTER/+OBSERVER; `tx.conf`/`rx.conf` deleted; `tests/test_protocol.c` extended (boot, toggling, independence, NULL guards). Compile-time role mechanism: fully removed (no ROLE Kconfig, no fragments, no EXTRA_CONF_FILE; confirmed absent from generated `.config`).

Serial: TX mode consumes exact OBS/CLR from uart0/VCOM 115200 8N1 (invalid/overlong ignored); RX mode emits deduped OBS/CLR via verified uart0 printk path and never consumes serial; role entry clears/flushes UART so stale bytes can't become commands. BLE: same UUID/version/state protocol; TX advertises / RX scans with per-PHY params; switches tear down before starting the new side; PHY preserved across role changes.

Build (ONE, `nrf52840dk/nrf52840`, NCS v3.2.3, pristine, exit 0, zero warnings): `west -z C:/ncs/v3.2.3/zephyr build -p always -b nrf52840dk/nrf52840 firmware/transceiver -d build/transceiver` → `build/transceiver/transceiver/zephyr/zephyr.hex` (360796 B), `.elf` (1460920 B), `merged.hex`; FLASH 128248 B (12.23 %), RAM 27236 B (10.39 %); `.config`: BT+BROADCASTER+OBSERVER, GPIO, SERIAL/CONSOLE/UART_CONSOLE, PHY_CODED+CODING_SELECTION, BLINK 500, no ROLE options; ELF contains both TX and RX paths. Host test compiles warning-free (ARM object, exit 0) but cannot execute here (no host C compiler); vectors verified by inspection.

System-design files changed: `system/system.md`, `system/control-signal-path.md`, root `README.md`, `firmware/README.md`, `decision-logs/DL-004-*` (banner), `decision-logs/DL-007-*` (banner), `decision-logs/DL-008-*` (new), `decision-logs/README.md` (index). Inspected-but-unchanged: `session-logs/2026-09-17.md` (historical session record), `robotics/README.md` (no transceiver content), `firmware/tools/rx_logger.py` (role-agnostic line reader), `MUSE_SESSION_LOG.md` history (protected engineering record). Contradiction re-grep: no active doc contradicts; only history, superseded records (bannered), and negation statements remain.

Hardware interaction: No hardware flashing, erase, recovery, debug connection, or target modification was performed. Attached nRF52840 left erased; second board absent.

### Changes made

- Modified: `firmware/transceiver/src/main.c`, `src/protocol.h` (extended), `Kconfig`, `prj.conf`, `firmware/README.md`, `system/system.md`, `system/control-signal-path.md`, `README.md`, `decision-logs/DL-004-*`, `decision-logs/DL-007-*`, `decision-logs/README.md`.
- Deleted: `firmware/transceiver/tx.conf`, `rx.conf` (tracked deletions, uncommitted).
- Created: `decision-logs/DL-008-transceiver-runtime-roles-single-image.md`; `firmware/transceiver/tests/test_protocol.c` and `src/protocol.h` remain untracked from prior prompt (still uncommitted).
- Rebuilt (gitignored): `build/transceiver/`; removed stale `build/transceiver-tx|rx/`; reused `build/.zephyr-cache`.
- Temp: `single_build.log`, `test_protocol2.o` under `...\Temp\opencode\`. Appended this entry. No commits, no pushes; unrelated untracked artifacts preserved.

### Conclusion

- Single-image runtime-role architecture implemented, documented across firmware/system/decisions, and built warning-free; protocol, dedup, UART contract, and PHY behavior preserved with role/PHY orthogonality and explicit switch boundaries.
- Only non-hardware validation complete; two-board same-image exchange, on-hardware buttons/LEDs, and host-test execution remain unproven until hardware + host compiler are available.
- No causality claim about the original BSOD fix (cable, host install, probe firmware all changed).

### Next boundary

Flash the single image on both boards and run the two-board smoke + role/PHY switching validation only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Requested-vs-active role + host-test evidence correction

### User request

Two targeted corrections, preserving BLE behavior and the established `CLR` default: (1) requested role vs active role — Button-2 press commits to TX/RX only after its BLE transport starts; LEDs reflect the active role; failed advertising/scanning start must not show a normal TX/RX pattern; keep boot and RX→TX `CLR` default. (2) Resolve host-test reporting contradiction — determine exactly what compiler, if any, compiled `tests/test_protocol.c` and the exact command; correct the record to inspection-only if never compiled; do not install a compiler. Update only affected code/docs; pristine-build single image for `nrf52840dk/nrf52840`; no flash/J-Link; log result.

### Actions performed

- Determined host-test compiler evidence: `arm-zephyr-eabi-gcc --version` (Zephyr SDK 0.17.0, GCC 12.2.0); confirmed no `gcc`/`cl`/`clang` on PATH; recompiled the test with the exact prior command (`-c -Wall -Wextra -std=c99`), exit 0, no warnings, object only.
- Edited `src/main.c`: added `transport_active` flag gating `leds_toggle`; reordered `switch_to_rx`/`switch_to_tx` to commit `mode.role` only after successful transport start, with previous-side restore and dark-LED total-failure path; set `transport_active=true` after boot TX start. Untouched: `CLR` boot default, RX→TX `CLR` re-init, protocol, dedup, PHY switching, UART framing.
- Edited `firmware/README.md` (role-entry steps, failure semantics, validation host-test wording) and `decision-logs/DL-008-*` (failure bullet). Prior log entries left intact.
- Pristine `west` build of `build/transceiver`; verified exit code, warnings, artifacts, memory, `.config` role/BT-role options; `git status`. No flash/erase/recovery/debug; J-Link/nRF tools never invoked.

### Results

Requested vs active role: `mode.role` now changes only after `rx_transport_start` / `tx_transport_start` succeeds; on failure the firmware restores the previous side when possible and keeps the old active role. LED failure behavior: restore success → normal indication of the still-active role; total failure (neither side runs) → role LEDs forced off with blinking suspended (never a normal TX/RX pattern), `led2` PHY indicator unaffected; next Button-2 press retries. Boot and RX→TX `CLR` default unchanged.

Host-test evidence correction: `tests/test_protocol.c` WAS compiled — exactly once per prompt with `arm-zephyr-eabi-gcc.exe -c -Wall -Wextra -std=c99 -o <temp>/test_protocol[N].o`, exit 0, zero warnings — but that is an ARM cross-compiler producing an unlinked object file, so the test was never linked and never executed. No host-targeted compiler exists on this machine. Prior "compiles warning-free but could not execute" wording was imprecise in implying host compilation; `firmware/README.md` now states the exact cross-compiler, command, object-only outcome, and inspection-only status of the vectors. Prior session-log entries preserved as history; this entry is the correction.

Build: pristine, `nrf52840dk/nrf52840`, NCS v3.2.3, exit 0, zero warnings; `zephyr.hex` 361156 B, `merged.hex` 361074 B; FLASH 128364 B (12.24 %), RAM 27236 B (10.39 %); `.config` has BROADCASTER+OBSERVER, no `TRANSCEIVER_ROLE_*` (only unrelated `BT_LL_SOFTDEVICE_MULTIROLE`).

Hardware interaction: No hardware flashing, erase, recovery, debug connection, or target modification was performed.

### Changes made

- Modified: `firmware/transceiver/src/main.c`, `firmware/README.md`, `decision-logs/DL-008-transceiver-runtime-roles-single-image.md`.
- Rebuilt (gitignored): `build/transceiver/`. Temp: `rolefix_build.log`, `test_protocol3.o`.
- Appended this entry to `MUSE_SESSION_LOG.md`. No commits, no pushes.

### Conclusion

- Role indication is now truthful: LEDs follow the running transport, with an explicit dark-LED fault state; `CLR` defaults and all BLE/UART behavior preserved.
- Host-test record corrected to exact evidence: cross-compiled object only, never executed, inspection-only vectors.
- Single image builds warning-free; all hardware validation still pending second board.

### Next boundary

Flash the single image on both boards and run the two-board smoke + role/PHY switching validation only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Decision-governance migration to subsystem-environment IDs

### User request

Documentation/governance migration only, no firmware changes, no hardware access. Replace `DL-###` naming with `<subsystem>-<environment>-<NNNN>-<decision-name>.md` (sequence local to each pair, chronological, no invented taxonomy, no extra layers). Update headings to `# Decision:` + `**ID:**`, preserve `DL-###` as `Previous ID`, document the convention in the existing governance file, migrate all 8 records, update every active reference (leaving historical logs intact), rebuild the index with Previous-ID column, verify (no active DL IDs, no old filenames, pattern/sequence/link/duplicate checks), report, log.

### Actions performed

- Read `MUSE_SESSION_LOG.md` (history preserved), confirmed no `AGENTS.md`, listed `decision-logs/`, read all 8 decision records (incl. DL-002's inline `## Archived Decisions` convention), index, and all repo files referencing decisions.
- Classification from evidence only (subsystems `ble`/`robot`, environments `runtime`/`ros`/`hardware` — all prompt-established and repo-supported; nothing invented): ble-runtime = DL-001/004/007/008 chronologically 0001–0004; robot-runtime = DL-002/005 → 0001/0002; robot-ros = DL-003 → 0001; robot-hardware = DL-006 → 0001. DL-002's archived 09-15 platform sub-decision rides along inline per its established archive convention.
- Renamed via `git mv` (6 tracked) + filesystem move (DL-007/DL-008, never committed).
- Rewrote all 8 headings (`# Decision:`, `**ID:**`, `**Previous ID:**`), updated supersede refs to new IDs, updated live cross-refs (DL-001→robot-ros-0001, DL-005→robot-runtime-0001, DL-006→new filename, DL-008 body→ble-runtime-0003); left archived/historical prose intact.
- Rebuilt `decision-logs/README.md` with convention section + new index table; updated root `README.md` link and `firmware/README.md` ID mentions. Firmware sources untouched (still reference legacy IDs in comments; reported, not modified per constraint).
- Verified with filename-pattern/ID-uniqueness/link-resolution script (PASS, 8/8) plus repo-wide `DL-` grep audit; `git status`. No builds, no firmware edits, no hardware commands.

### Results

Migration map (previous → new, states unchanged except noted):

- DL-001 → `ble-runtime-0001-wifi-to-ble-communication.md` (Accepted)
- DL-004 → `ble-runtime-0002-shared-transceiver-firmware.md` (Superseded by ble-runtime-0004)
- DL-007 → `ble-runtime-0003-transceiver-phy-modes-button-switching.md` (Superseded, PHY retained)
- DL-008 → `ble-runtime-0004-transceiver-runtime-roles-single-image.md` (Accepted — current)
- DL-002 → `robot-runtime-0001-dual-robot-architecture.md` (Accepted — current; inline 09-15 archive preserved)
- DL-005 → `robot-runtime-0002-husky-radar-obstacle-footprint.md` (Accepted)
- DL-003 → `robot-ros-0001-jackal-control-serial-ssh-ros.md` (Accepted, initial impl)
- DL-006 → `robot-hardware-0001-husky-power-troubleshooting-conventions.md` (Accepted)

Verification: no `DL-*` filenames remain; no active record uses a `DL-###` primary ID (remaining mentions are `Previous ID` metadata, bannered historical bodies, the inline DL-002 archive, and protected session-log history); all 8 filenames match the pattern; per-pair sequences unique and chronological; all relative links resolve (script PASS); no new subsystem/environment invented.

Hardware interaction: No hardware flashing, erase, recovery, debug connection, or target modification was performed.

### Changes made

- Renamed 8 decision files (6 via `git mv`, 2 via filesystem move as they were never committed).
- Modified: all 8 records (headings/IDs/refs), `decision-logs/README.md` (convention + index), root `README.md`, `firmware/README.md`.
- Unmodified as required: firmware sources, build config, all other docs; unrelated untracked artifacts preserved.
- Temp: `check_decisions.py` under `...\Temp\opencode\`. Appended this entry. No commits, no pushes.

### Conclusion

- Decision governance migrated: convention documented, all records renamed with pair-local chronological numbering, references updated, history traceable via Previous-ID + git.
- Only remaining old-ID occurrences are intentional (metadata, bannered history, inline archive, session logs).

### Next boundary

Flash the single image on both boards and run the two-board smoke + role/PHY switching validation only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Firmware legacy-ID cleanup + pristine rebuild

### User request

Cleanup only before flashing: replace legacy `DL-###` references in active firmware source/docs with canonical new IDs (DL-007→ble-runtime-0003, DL-008→ble-runtime-0004); leave session logs, Previous-ID metadata, archived prose, and other intentional retentions; no behavior change. Then confirm zero active firmware `DL-###` refs repo-wide, run one pristine `nrf52840dk/nrf52840` build, report files/IDs/remnants/build; no flash/J-Link; log result.

### Actions performed

- Grepped `firmware/` for `DL-00[1-8]`: 5 comment-only hits (main.c header, protocol.h ×2, Kconfig, test_protocol.c). Replaced DL-008→ble-runtime-0004 (×4) and DL-004→ble-runtime-0002 (×1, protocol.h dedup-rules comment). No code, config, or doc-semantics change.
- Re-grepped `firmware/`: zero matches. Repo-wide `*.md` audit for remaining `DL-00[1-8]`.
- Pristine `west` build of `build/transceiver`; verified exit code, warnings, artifacts, memory. No flash/erase/recovery/debug; J-Link/nRF tools never invoked.

### Results

Replacements: DL-008→ble-runtime-0004 in `src/main.c`, `src/protocol.h` (mode comment), `Kconfig`, `tests/test_protocol.c`; DL-004→ble-runtime-0002 in `src/protocol.h` (dedup-rules comment).

Remaining `DL-` occurrences (all intentional): `Previous ID` metadata in all 8 records + index column; bannered historical bodies (ble-runtime-0002/0003, incl. DL-004 mentions in 0003 body); DL-002 inline 09-15 archive heading; protected `MUSE_SESSION_LOG.md` history. Zero in active firmware source/docs.

Build: pristine, `nrf52840dk/nrf52840`, NCS v3.2.3, exit 0, zero warnings; artifacts regenerated; FLASH 128364 B (12.24 %), RAM 27236 B (10.39 %) — identical footprint, consistent with comment-only change.

Hardware interaction: No hardware flashing, erase, recovery, debug connection, or target modification was performed.

### Changes made

- Modified (comments only): `firmware/transceiver/src/main.c`, `src/protocol.h`, `Kconfig`, `tests/test_protocol.c`.
- Rebuilt (gitignored): `build/transceiver/`. Temp: `cleanup_build.log`.
- Appended this entry to `MUSE_SESSION_LOG.md`. No commits, no pushes.

### Conclusion

- Active firmware/source tree is free of legacy decision IDs; behavior bit-identical; single image builds warning-free.
- Ready boundary unchanged: flash only with second board present and explicit authorization.

### Next boundary

Flash the single image on both boards and run the two-board smoke + role/PHY switching validation only when the second nRF52840 DK is connected and explicitly authorized; flashing remains forbidden until then.

## 2026-09-28 — Flash executed + single read-only debug check (secured target, early-fault evidence)

### User request

Flash the connected nRF52840 DK once with `build/transceiver/transceiver/zephyr/` artifacts via normal NCS workflow; then single-board validation only (boot, TX/CLR/S=8 defaults, LEDs, buttons, UART; no BLE, second board absent); no code changes unless a real defect appears; single flash attempt with BSOD caution. Follow-up: exactly ONE read-only debug check (reset vector, SP, PC/SP/xPSR, core state, CFSR/HFSR/MMFAR/BFAR, PC→ELF mapping; halt only to read; no memory modification), plus ELF symbol identification. Report and log.

### Actions performed

- Verified artifacts newer than sources (`zephyr.hex`/`merged.hex` 13:51:47 > sources 13:50:31); single `app` partition at 0x0, no bootloader (MCUboot dirs are module sources only).
- Confirmed VCOM `COM8`/`COM9` enumerated pre-flash; 4 s serial silence on both (expected for TX/CLEAR).
- ONE flash: `west -z C:/ncs/v3.2.3/zephyr flash -d build/transceiver` (runner nrfutil, board 001050670813): erase ranges, program `merged.hex`, verify passed, reset, "flashed successfully", exit 0.
- Post-flash: 15 s COM8 capture = 0 bytes; user reported no LED activity ("nothing happening").
- ONE read-only J-Link Commander V9.80 session (`USB/Device/SWD/1000/Connect/h/regs/mem32 0/2/mem32 E000ED28,5/g/Exit`), exit 0: full register + fault-register + vector reads, then resumed (`g`) and exited.
- Host-side artifact forensics (no hardware): `.config` APPROTECT options, UICR records in `merged.hex`, vector table from `zephyr.hex`, `nm`/`objdump` on `zephyr.elf`; boot-time + minidump stability check.
- No erase/flash/recover beyond the one authorized flash; no memory writes; no code changes.

### Results

Flash result: PASS (program + verify + reset, exit 0). J-Link/target result: probe opened (S/N 1050670813, VTref 3.3 V), SW-DP/APs/Cortex-M4 identified, session exit 0. Windows stability: stable throughout (boot 10:40:36 unchanged, no new dumps; only the two preserved dumps).

Core state (read-only session):

- On `Connect`, J-Link reported `Device will be unsecured now` (InitTarget 3.39 s): the target WAS debug-secured (APPROTECT) at connect time. Unsecuring an nRF52 performs a mass erase — the flash was therefore emptied by the unlock itself, before any reads.
- `mem32 0x0,2` = `FFFFFFFF FFFFFFFF`: reset vector and initial SP read back erased (expected post-erase; NOT the programmed values).
- Halted-state registers: PC=`FFFFFFFE`, SP/MSP=`FFFFFD8`, R0–R12=0, LR=`FFFFFFF9`, xPSR=`01000003` (IPSR=3, HardFault), all FP regs 0.
- Fault registers: CFSR=`00001001` (MMFSR IACCVIOL + BFSR STKERR), HFSR=`40000000` (FORCED), DFSR=`00000001` (HALTED, set by our halt), MMFAR/BFAR not meaningful (valid bits clear).
- Interpretation: every register/fault value above is the aftermath of booting an ERASED chip plus our deliberate halt — instruction fetch from invalid vectors → forced HardFault → lockup. It is NOT a snapshot of the application failing.

PC→symbol mapping: PC `FFFFFFFE` does not map into the ELF; no app function corresponds to it. Expected programmed vectors from build artifacts: MSP=`20005380`, reset word=`01002FFD` → handler `01002FFC` (inside `text` 0x100–0x1DD74); `_vector_table`@0x0, `main`@0x1230c. (No `__reset` symbol by that name in this Zephyr build; entry is the vector-table reset word above.)

Whether the app is executing: unknown — the unlock-erase destroyed the evidence. Pre-erase state (running vs faulted) cannot be reconstructed from post-erase reads.

Early-fault evidence: none obtainable from this session (see above). Two established facts constrain the next step instead: (1) user-observed dark LEDs + silent UART after a verified flash/reset, and (2) `CONFIG_NRF_APPROTECT_USE_UICR=y` is set in the build (NCS default; no UICR records in `merged.hex`, so the lock is applied by the firmware's boot-time UICR driver, not by the programmed image — meaning the chip was accessible at flash time and secured itself on first boot).

### Changes made

- Target nRF52840: flashed once (verified), then mass-erased as a side effect of the debug-unlock in the authorized read-only check. Net device state: ERASED (as before the flash). No firmware/config/repo source changes.
- Temp scripts/logs: `jlink_readonly_check.jlink`, `flash1.log`. Appended this entry. No commits, no pushes.

### Conclusion

- Flash pipeline works (program/verify/reset, Windows stable); VCOM enumerates; but on-board execution after reset is unproven — dark LEDs + silent UART persist as the unexplained observation.
- The debug session proved the target secures itself on first boot (APPROTECT via NCS default UICR driver) and therefore any future debug attach will again unsecure+erase unless the image is built with debug access preserved or recovery is accepted.
- The register dump must NOT be cited as an application fault signature; it is a post-erase artifact.

### Next boundary

Most specific next step: host-side, decide the APPROTECT policy for development builds (keep NCS default and accept unsecure-erase on every debug attach, or disable for lab use); then, under a new explicit authorization, reflash once and, if LEDs stay dark, halt at the reset vector immediately after reset to capture a true pre-erase fault state (PC, LR, CFSR/HFSR) before any unlock can destroy it.

## 2026-09-28 — APPROTECT policy determined; UICR-dev-open defeated by flash erase; debug STOPPED per constraint

### User request

Determine/implement dev APPROTECT policy (inspect exact NCS config/sources, explain USE_UICR, verify symbols locally, smallest dev-only change, explicit production implications, build verification), then one flash/debug cycle: flash, verify, reset, halt at reset vector, capture PC/SP/xPSR/regs/vectors/CFSR/HFSR/MMFAR/BFAR/DFSR, map to ELF, step toward main, find earliest divergence, check accessibility without unsecure. Constraints: no further unsecure/erase after diagnostic flash; single variable; no unrelated changes; STOP (don't unlock) if locked again.

### Actions performed (all verified from local source, no guessing)

- Kconfig: `zephyr/soc/nordic/Kconfig` choice `NRF_APPROTECT_HANDLING`, `default NRF_APPROTECT_USE_UICR` for nRF52X. Our `.config` has it (untouched default); no Kconfig on nRF52 can force-open (DISABLE is NRF54L-only, USER_HANDLING excludes 52X, LOCK is worse).
- Call chain: `system_nrf52840.c` includes `system_nrf52.c` → `SystemInit()` unconditionally calls `nrf52_handle_approtect()` (`system_nrf52_approtect.h`); without `ENABLE_APPROTECT` (unset) it executes `NRF_APPROTECT->DISABLE = NRF_UICR->APPROTECT`. UICR erased = `0xFFFFFFFF` = locked at every boot, pre-main.
- Magic/address from MDK: UICR base `0x10001000` + APPROTECT offset `0x208` = `0x10001208`; `UICR_APPROTECT_PALL_HwDisabled = 0x5A`.
- Decision (smallest dev-only change, zero firmware delta): one-time device-side `nrfjprog --memwr 0x10001208 --val 0x5A --verify` (exit 0, "Verified OK"), confirmed by `--memrd` = `0000005A`. Production `prj.conf`/build untouched, so production images keep the locking default.
- Noted new observation: repeated `SeggerBackend JLinkARM.dll error -256` lines on both nrfjprog ops, operations still verified OK, Windows stable.
- ONE flash: `west flash -d build/transceiver` (nrfutil, board 001050670813): erase/program/verify/reset all OK, exit 0.
- ONE J-Link halt-at-reset session (`Connect/r/regs/mem32 0,2/mem32 faults/g/Exit`), exit 0. `Connect` reported `Device will be unsecured now` → STOPPED further debug per constraint (no additional sessions).
- Host-side forensics only afterward: full `flash2.log`, `nrfutil device program --help` (default `chip_erase_mode=ERASE_ALL` erases UICR+flash), runner source (`nrfutil.py` passes no explicit mode → nrfutil default applies).

### Results

1. Mechanism: `NRF_APPROTECT_USE_UICR` (Kconfig default) → SystemInit `DISABLE = UICR.APPROTECT` → erased UICR locks SWD pre-main, every boot. CPU execution unaffected by the lock itself.
2. Change made: device UICR `0x10001208 = 0x5A` (HwDisabled), verified by read-back. No firmware/Kconfig change — none exists that keeps nRF52 debug open; production policy preserved explicitly.
3. Production implications: `0x5A` UICR = full SWD access (read firmware, dump flash); never ship; dev boards must be recovered/erased before production use; shipped builds (unchanged config) lock by default.
4. Build evidence: no rebuild required (firmware byte-identical; current image already built pristine). `.config` still `USE_UICR=y` by design.
5. Flash/verify: exit 0, "flashed successfully", verify passed, reset done.
6. Earliest valid post-reset state: NOT obtained — connect auto-unsecured (mass erase) before any read, so vectors read `FFFFFFFF/FFFFFFFF`, regs show empty-flash reset-halt (`PC=FFFFFFFE`, `SP=FFFFFFFC`, DFSR=`08` VCATCH from our `r`, CFSR/HFSR zero). These are erase artifacts, not app evidence.
7. PC/LR mapping: N/A (erased). Expected from artifacts (unchanged): MSP `20005380`, reset → `01002FFC`, `main` `0x1230c`.
8. Reset handler / main reached: unproven this cycle (evidence destroyed by auto-unsecure).
9. Earliest failure point: none established; prior dark-LED observation still unexplained.
10. SWD accessible afterward: NO — device re-locked; per constraint, no unlock attempted. Root cause of re-lock (host-side proof): the flash flow cleared the `0x5A` UICR (nrfutil default ERASE_ALL erases UICR+flash; runner passes no explicit mode), then the app boot re-locked from erased UICR. Verified sequence: UICR=`5A` read-back → only flash ran → locked at next connect.
11. Single next step: new authorized cycle in corrected order — flash app FIRST, then `nrfjprog --memwr UICR=0x5A` + verify, then `nrfjprog --reset` (no erase), then halt-at-reset capture. Nothing after the UICR write may erase; UICR survives app sector-erase/reset.

Hardware interaction: one `nrfjprog` UICR write (+verify/read-back), one `west` flash (program/verify/reset), one J-Link read-only session (auto-unsecure erased target; `r`/reads/`g`/exit; no memory writes). No further probe ops after the lock was observed. Net device state: ERASED + UICR erased (locked-on-next-boot).

### Changes made

- Device UICR.APPROTECT written `0x5A` (subsequently cleared by the flash flow — recorded, not re-attempted).
- No repo source/config changes. Temp: `flash2.log`, `jlink_halt_at_reset.jlink`.
- Appended this entry. No commits, no pushes.

### Conclusion

- Dev APPROTECT policy determined and verified from source: UICR-content-gated, Kconfig cannot force-open on nRF52, production default correctly left intact.
- The diagnostic cycle was defeated by erase ordering (flash wiped the dev-open UICR before boot); corrected order identified for the next authorized attempt.
- No application-fault evidence exists yet; empty-flash reads must never be cited as such.

### Next boundary

Awaiting authorization for one reordered cycle (flash → UICR 0x5A → verify → reset → halt-at-reset capture), then two-board validation once execution is proven.

## 2026-09-28 — Corrected flash order works; genuine boot fault captured (heap end-marker, both images)

### User request

Stop extended diagnostics; get firmware flashed and RUNNING (FLASH→BOOT→RUN) with recover/UICR/flash authorized; first priority boot, no elaborate dumps unless still failing. Follow-up (current): no reflash, no firmware changes; one halt-only inspection (PC/SP/LR/xPSR/CFSR/HFSR/MMFAR/BFAR, PC/LR→ELF, vectors vs ELF, GPIO P0 DIR/OUT/PIN_CNF for P0.13/14/15 derived from DTS active-low semantics); single evidence-backed execution boundary (not a hypothesis list); log result.

### Actions performed

- Corrected order executed: `nrfjprog --recover` (exit 0) → `--program merged.hex --sectorerase --verify` (exit 0) → `--memwr UICR 0x5A` + read-back `0000005A` (exit 0; recover had left UICR non-empty, auto-confirmed) → `--memrd 0x0` vectors `20005380/00012FFD` = ELF expectation → `--reset` (exit 0).
- Post-boot: UICR still `0x5A` (survived; SWD reads need no unsecure), COM8 silent, user: only power LED, nothing blinking.
- ONE live session (connect/h/regs/mem32s/g/exit, exit 0, no unsecure): core RUNNING (CycleCnt 7.2M), halted at PC `1D456`/`LR 1D45F`, IPSR=BusFault(5), CFSR/HFSR read; resumed after.
- T+0 reset serial capture (`reset_capture.py`: port open before `nrfjprog --reset`, 15 s): caught `***** BUS FAULT ***** Imprecise data bus error`, r0=`72B2` r1=`2003FFF8` r2=1 r3=`72A8` lr=`1BEFD` pc=`1BEFE`.
- Host-side mapping (objdump/nm/addr2line, heap.c/malloc.c sources): fault PC in `sys_heap_init` end-marker writes; sole `sys_heap_init` caller is `malloc_prepare` (`SYS_INIT, POST_KERNEL`); heap args sane (base `20006A68`, size `39598`, from `_end`=`20006A64`); thread-stack backtrace: `arch_switch_to_main_thread → z_thread_entry → bg_thread_main → z_sys_init_run_level → … → malloc → malloc_prepare → sys_heap_init`.
- Isolation: built stock Blinky (`build/blinky-ref`, exit 0), flashed it (`--sectorerase`, verified, UICR kept `5A`, reset) — Blinky ALSO BusFaults at boot with the identical signature (PC `40CE` after `set_chunk_size`, r1=`2003FFF8`, halt loop `4E00`), confirmed via second T+0 capture.
- Final inspection (current prompt, Blinky flashed): vectors `20001940/00000B31` match Blinky's own hex/ELF (`_vector_table`@0, `main`@0x100); PC `4E00` = `arch_system_halt` loop, LR `4E09`; CFSR=0/HFSR=0/DFSR=HALTED; GPIO P0 OUT=`0x60` DIR=`0x60` PIN_CNF[13,14,15]=`2,2,2`; DTS: led0/1/2 = P0.13/14/15 `GPIO_ACTIVE_LOW` (ON = driven LOW).

### Results

- Requested-vs-expected: the premise "transceiver firmware is flashed" is outdated — the board currently runs the Blinky reference image (flashed for isolation, reported at the time). All GPIO conclusions below are against Blinky; our image needs a reflash (not authorized this prompt) before any app-level validation.
- PC/LR→symbol: transceiver fault PC `1BEFE` = `sys_heap_init` end-marker write sequence, LR back into `sys_heap_init`; halt PC `1D456` = `arch_system_halt+0xe` infinite loop (matches BASEPRI=`0x40` set by its prologue). Blinky: fault `40CE` same sequence; halt `4E00` same loop.
- Fault registers: imprecise data bus error, no status bits (CFSR/HFSR zero), BFAR invalid — consistent in both images; post-erase reads from earlier sessions are not app evidence and are excluded.
- GPIO evidence: P0.13/14/15 are INPUTS (`DIR=0`, `PIN_CNF=2`) — LED driver output never configured; P0.5/6 outputs = uart0 console (driver up, banner printed). So `main()` never runs in either image; boot dies in POST_KERNEL init.
- Strongest proven boundary: execution reaches Zephyr POST_KERNEL init and faults inside the libc malloc-arena init while writing heap metadata at the top of SRAM (both faults land on end-marker writes near `0x2003FFF8` with internally consistent heap math); `main()` is never reached. No application code of ours executes before the fault.
- Firmware attribution: evidence is NOT strong enough to attribute to firmware — the identical failure in stock Blinky (which contains none of our code) exonerates application logic. Open discriminator: top-of-SRAM writes faulting (hardware/power/protection) vs an earlier bad write surfacing late. MPU was checked (`CONFIG_ARM_MPU=y` in both) but MPU violations are precise MemManage faults, contradicting the observed imprecise BusFault, so MPU is excluded as the direct cause.

Hardware interaction: recover, sector-erase program+verify (transceiver, then Blinky), UICR writes/read-backs, resets (nrfjprog), and read-only J-Link sessions (connect/halt/regs/mem-reads/go; one `r` reset-catch); no flash-breakpoint/memory writes to target code or data; Windows stable throughout, no new dumps. Net device state: Blinky flashed, UICR `0x5A`, SWD open, app faulted in halt loop.

### Changes made

- Reference build `build/blinky-ref/` (gitignored) for isolation; no repo source/config changes this prompt.
- Temp: `reset_capture.py`, `stackdump.log`, `gpio_inspect.log`, `jlink_*.jlink`, `blinky_build*.log`.
- Appended this entry. No commits, no pushes.

### Conclusion

- Corrected flash order (recover → sector-erase program → UICR `0x5A` → verify → reset) works: programming verifies, UICR survives, SWD stays open with no unsecure.
- The dark-board symptom is a genuine Zephyr-boot BusFault in malloc-arena init, reproduced identically on stock Blinky — not an app-logic defect, not a flash failure, not APPROTECT.
- Next discriminators (require authorization): pure-read sweep of top-of-SRAM; and/or a `CONFIG_COMMON_LIBC_MALLOC_ARENA_SIZE=0` diagnostic build (skips heap init entirely) to split bad-RAM-region from earlier-bad-write.

### Next boundary

Reflash the transceiver image (authorized separately) only after deciding the next discriminator; two-board validation remains blocked until an image provably boots.

## 2026-09-28 — Root cause proven: physical chip is nRF52833, heap exceeds real SRAM (Case B)

### User request

Discriminate SRAM-hardware failure (A) vs invalid heap/linker config (B) vs subtler fault (C): (1) hardware SRAM size from FICR; (2) controlled volatile SRAM write/read (save/pattern/complement/restore) at low/mid/top/`0x2003FFF8`, flash untouched; (3) exact heap bounds for both ELFs vs physical boundary; (4) Zephyr/libc config behind the pre-main malloc path. No reflash. Single evidence-backed classification + log.

### Actions performed

- Host-side: `_end`/`z_malloc_heap` from both ELFs; `HEAP_BASE` literals from `malloc_prepare` disassembly; libc/MPU `.config` comparison; `SYS_INIT(malloc_prepare, POST_KERNEL, …)` source confirmation.
- J-Link session 1 (connect/h/regs/FICR `0x10000100`×5/baseline RAM reads/g/exit, exit 0, no unsecure).
- Verified FICR INFO offsets against MDK `nrf52840.h` (PART+0x00, RAM+0x0C, FLASH+0x10).
- J-Link session 2 (connect/h/FLASH-size word/save+w4/memrd two-pattern/verify/restore+verify at 4 addresses/g/exit, exit 0, no unsecure, flash untouched).
- No erase/flash/recover; only volatile SRAM words written and restored; Windows stable throughout.

### Results

- Hardware-reported: FICR PART=`0x00052833`, RAM=`0x00000080` (128 KB), FLASH=`0x00000200` (512 KB) — the physical target is an **nRF52833**, valid SRAM `0x20000000–0x2001FFFF`. `0x2003FFF8` is NOT valid RAM on this device. Both images were built for `nrf52840dk/nrf52840` (256 KB RAM assumption); the connected board is almost certainly an nRF52833 DK, not nRF52840.
- SRAM write/read: `0x20000000` ✓✓, `0x20010000` ✓✓, `0x2001FFF0` ✓✓ (both patterns read back, originals restored and verified); `0x2003FFF0` writes accepted by the tool but read back `0x00000000` (patterns do not stick). RAM works everywhere it physically exists.
- Heap bounds (calculated): TX `_end`=`0x20006A64` → base `0x20006A68`, size `0x39598`, end ≈`0x2003FFF8`; Blinky `_end`=`0x20001980` → base `0x20001980`, size `0x3E680`, end ≈`0x2003FFF8`. Both heaps extend 128 KB past the physical SRAM end (`0x20020000`).
- Config behind the path: both builds picolibc + `COMMON_LIBC_MALLOC=y` + `ARENA_SIZE=-1` + `KERNEL_INIT_PRIORITY_LIBC=35` → `SYS_INIT(malloc_prepare, POST_KERNEL, …)` runs arena init before `main()` in every app incl. stock Blinky; sole `sys_heap_init` caller is `malloc_prepare`.
- Mechanism closed: end-marker chunk writes at heap end (~`0x2003FFF8`, beyond RAM) → imprecise data bus error during POST_KERNEL → `arch_system_halt` loop; `main()` never runs; LEDs never configured; UART already up so the banner prints.

### Changes made

- None to repo sources/config. Temp: `jlink_ram_baseline.jlink`, `jlink_ram_test.jlink`, `ram_baseline.log`, `ram_test.log`, `check_decisions.py` (prior prompt).
- Appended this entry. No commits, no pushes.

### Conclusion

- **Classification: Case B — invalid heap/linker configuration.** SRAM works where it exists; the generated heap exceeds physical SRAM because the image targets the wrong SoC. Not a RAM defect, not app logic, not MPU.
- Fix direction (separate authorized prompt): build for `nrf52833dk/nrf52833` and reflash (also re-checks SoftDevice-controller SoC compatibility and the `nrf52840dk` board references in docs).

### Next boundary

Awaiting authorization to build for `nrf52833dk/nrf52833` and reflash; two-board work stays blocked until an image provably boots.

## 2026-09-28 — Retarget to nRF52833 DK: docs corrected, single image rebuilt

### User request

Fix target mismatch (FICR-proven nRF52833, 128 KB SRAM `0x20000000–0x2001FFFF`, prior `nrf52840dk` builds overran SRAM): identify correct board target from board/repo/hardware evidence (not MCU name alone); make it canonical; correct active docs claiming nRF52840; preserve history; update materially affected system/decision records; pristine build; verify MCU/RAM/SRAM-end/heap/runtime/PHY/buttons from ELF/map/config; no flash; report.

### Actions performed

- Verified `nrf52833dk/nrf52833` exists in NCS v3.2.3 with identical required aliases/pins (`led0/1/2` P0.13/14/15 active-low, `sw0`/`sw1` Buttons 1/2, uart0 console 115200) — no firmware source change needed.
- Grepped repo for active `nRF52840` claims: only `firmware/README.md`, `tests/test_protocol.c` comment, `ble-runtime-0004`; corrected all (board target, build commands, validation section with new numbers, two-board line, test comment, decision alias note), each with explicit correction annotation; history (session log, Previous-ID, banners, archive) preserved.
- Pristine `west` build `-b nrf52833dk/nrf52833` into `build/transceiver` (exit 0, zero warnings); verified `.config` (`SOC_NRF52833`, board target, BT+broadcaster+observer, GPIO, UART console, coded-PHY+coding-selection, no ROLE options), `build_info.yml` board, ELF symbols/strings, artifacts. No flash/erase/probe ops.

### Results

- Physical board/MCU: nRF52833 (FICR PART `0x52833`, 128 KB RAM, 512 KB flash); working identification nRF52833 DK (model marking to be visually confirmed when convenient).
- Old target: `nrf52840dk/nrf52840`. New canonical target: `nrf52833dk/nrf52833`.
- ELF: `_end`=`0x200055E4`, heap base `0x200055E8` size `0x1AA18` end exactly `0x20020000` — nothing exceeds `0x2001FFFF`. Runtime TX+RX paths, OBS/CLR, S=8/1M transport code all present; buttons need no Kconfig (GPIO+aliases, `#error`-guarded, DTS-verified).
- Artifacts: `zephyr.hex` 326104 B, `merged.hex` 326048 B; FLASH 115916 B (22.11 % of 512 KB), RAM 21988 B (16.78 % of 128 KB).
- Remaining intentional `nRF52840` refs: session-log history; explicit correction notes in `firmware/README.md` + `ble-runtime-0004`.
- Hardware interaction: none — no probe commands of any kind this prompt.

### Changes made

- Modified: `firmware/README.md`, `firmware/transceiver/tests/test_protocol.c` (comment), `decision-logs/ble-runtime-0004-*`.
- Rebuilt (gitignored): `build/transceiver/`. Temp: `build_833.log`.
- Appended this entry. No commits, no pushes.

### Conclusion

- Target mismatch fixed at the documented canonical level; image now fits physical SRAM with margin; SoftDevice controller linked for the 52833 SoC (link success).
- Next: authorized flash + boot validation on the nRF52833.

### Next boundary

Awaiting authorization to flash the `nrf52833dk` image and validate boot/LEDs/buttons/UART; two-board work stays blocked until then.

## 2026-09-28 — Second board verified (nRF52833) and flashed with corrected image

### User request

Second board connected (first disconnected): verify MCU, flash with corrected `nrf52833dk` image, boot-validate. Single-board validation only.

### Actions performed

- Enumerated probes: only `1050611489` visible (first board `1050670813` absent — user swapped, not added); VCOM pair shifted across resets (stale `Unknown` ghost ports accumulate; current OK pair `COM13/COM14`, MI_02/MI_00).
- FICR read (`--snr 1050611489 --memrd`): PART=`0x52833`, RAM=`0x80`, same pattern as board 1 → nRF52833, 128 KB. Proceeded.
- `--snr 1050611489 --program merged.hex --sectorerase --verify` (exit 0, verify OK) → `--memwr UICR 0x5A` + read-back `0000005A` → vectors `20003EE8/00012E25` (nrf52833 image) → `--reset`.
- T+0 capture on `COM14` (MI_00 = target uart0; `COM7` from before reset was a stale ghost): clean 99-byte boot banner, no fault.
- No erase/recover beyond sector-erase program; no memory writes except UICR dev-open value; Windows stable.

### Results

- Second board: nRF52833, flashed + verified + UICR dev-open + reset, clean boot, no heap fault. Same corrected image as board 1.
- UART mapping lesson: on these DKs the target console is the MI_00 CDC port (COM8/COM14 here), but Windows COM numbers shift on re-enumeration — always re-resolve MI_00, never assume persistence.
- Net state: board 2 running corrected image; board 1 disconnected (still flashed with same image from before).

### Changes made

- Target 2: programmed, UICR set, reset. No repo changes. Temp: none new (reused scripts).
- Appended this entry. No commits, no pushes.

### Conclusion

- Both physical boards are nRF52833 and both now carry the corrected image. Two-board over-air validation is unblocked as soon as both are connected simultaneously.

### Next boundary

Reconnect board 1 alongside board 2, then run the README smoke test (TX stays, Button 2 → RX, logger, OBS/CLR single-record checks) plus button/LED cross-checks.

## 2026-09-28 — Acknowledgment, no action

### User request

Acknowledged the completed second-board flash/boot validation ("great!!!"). No new task.

### Actions performed

None. No commands, no file changes, no hardware access.

### Results

No new evidence. Both boards remain flashed with the corrected `nrf52833dk` image (board 1 disconnected, board 2 connected and running).

### Changes made

`None` (this log entry only).

### Conclusion

Session state unchanged; two-board validation still pending both boards connected.

### Next boundary

Reconnect board 1 alongside board 2, then run the README smoke test plus button/LED cross-checks.

## 2026-09-28 — Correction: no log entries were ever lost (prior scare retracted)

A verification scare during the sessions restructure claimed six log
entries were lost. Full re-verification (complete header listing,
byte counts, content markers) proves that false: every prompt of the
day is present exactly once, in order, lines 5–1063+. The scare came
from a truncated console listing (the Unicode `→` in the smoke-test
title crashed the listing tool mid-file) plus my misread of the tail —
not from missing data. The "BACKFILL" reconstruction below is therefore
redundant with the real entries that follow it; it is retained
unaltered as a record of the mistake, not as source of truth. Rule
adopted: verify with encoding-safe, complete listings before diagnosing
log integrity.

### Why this entry exists

After `MUSE_SESSION_LOG.md` moved from repo root to `2026-09-28/`,
six subsequent appends were issued against the stale root path. The tool
reported success, but verification now shows only one log file exists
(`sessions/2026-09-28/MUSE_SESSION_LOG.md`, ending at the ack entry) —
those six entries never persisted. This consolidated entry reconstructs
them factually from observed outputs and on-disk temp logs. Corrective
action: verify the log's real path (tail read) before every future append.

### B1. nRF52833 image flashed, application provably runs (was: flash-validation prompt)

- `nrfjprog --program build/transceiver/merged.hex --sectorerase --verify`
  (exit 0); UICR `0x5A` written after programming + read back; vectors
  `20003EE8/00012E25`; `--reset` (exit 0).
- T+0 capture: clean 99-byte Zephyr boot banner, no fault.
- Read-only sessions (`nRF52833_xxAA`): PC `19586` = `arch_cpu_idle`
  called from `idle`, IPSR=0, fault regs zero; main-stack backtrace
  `z_thread_entry → … → z_tick_sleep` with `bt_enable` absent →
  `main()` → `bt_enable()` (returned) → `transceiver_run()` → `k_sleep`.
- GPIO P0: DIR `E060`, OUT `6060` twice (~1 min apart): LED pins outputs,
  `led2` ON (S=8), role bits off-phase at both samples.
- UART COM8/COM9-class ports open at 115200, silent post-boot (correct
  for TX/`CLR`), writes accepted. LED-blink/buttons left for human.

### B2. Button/LED questions answered (no actions)

- Button 1 = PHY toggle S=8↔1M (role preserved, TX state kept, RX epoch
  reset, `led2` follows). LED3 ON = Coded S=8.

### B3. Second board verified and flashed

- Only probe `1050611489` visible (user swapped boards); FICR
  PART `0x52833` + 128 KB → nRF52833, proceeded.
- Same corrected image: sector-erase program + verify OK, UICR `0x5A`,
  vectors match, reset done. T+0 on `COM14` (MI_00; COM numbers shift,
  stale ghosts ignored): clean boot banner, no fault.

### B4. Two-board smoke test PASS

- Both probes (`1050670813` + `1050611489`); consoles `COM14` (MI_00) +
  `COM8` (MI_00). Trial found TX=`COM14`, RX=`COM8`.
- `OBS`→`['OBS']`, `CLR`×3→`['CLR']`, `OBS`×3→`['OBS']`; link left
  idling CLR. Proven: over-air exchange, propagation, dedup under
  repeats, episode semantics, S=8 operation, both UARTs.

### B5. Packet/files questions answered (no actions)

- Packet bytes: `13 16 116E…B47B 01 <00|01>`, UUID
  `7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11`, version/state rules, RX
  acceptance = byte-exact live proof (no sniffer in loop). File
  locations: session log, `Temp/opencode/`, decision logs; smoke output
  was console-only.

### B6. Validation folder + root cleanup + date bundles (as built)

- `firmware/validation/` created: `README.md`, two dated records,
  reusable `smoke_test.py` (py_compile OK). One bad README edit of mine
  briefly deleted the smoke-test steps — caught and restored verbatim
  plus validation pointers (verified by re-read).
- Root cleanup: 13 files + 4 scripts → `debug-evidence/` + index README;
  `tools/` removed; `.gitignore` += `*.dmp`, installer exe.
- `2026-09-28/` bundle, then restructured to
  `sessions/2026-09-28/` + `sessions/README.md` + full investigation
  README (7 parts). No commits/pushes; no hardware in these steps
  except the already-reported flashes.

### Conclusion

- Record repaired: all prompts above are now documented; future appends
  go to `sessions/2026-09-28/MUSE_SESSION_LOG.md` after a tail check.
- Engineering state unchanged: both boards run the corrected image,
  smoke PASS, human LED/button cross-checks pending.

### Next boundary

User commits/pushes (or instructs); then human LED/button cross-checks.

## 2026-09-28 — Two-board over-air smoke test PASS (TX→BLE→RX, dedup verified)

### User request

Both boards connected (user reports 1×RX + 1×TX roles set): serial validation of the link. No BLE-pairing scope change; single-board constraints lifted for two-board observation only.

### Actions performed

- Enumerated: probes `1050670813` + `1050611489`; OK VCOM pairs `COM14`(MI_00)/`COM13`(MI_02) + `COM8`(MI_00)/`COM9`(MI_02); stale ghost ports ignored.
- Wrote/run `smoke_test.py` (temp): opens both MI_00 consoles, trials both directions (OBS×3 → listen 3 s), then CLR×3 and OBS×3 single-record checks with buffers flushed between phases; restores CLR at end. No flash/erase/debug/probe ops; Windows stable.

### Results

- Pairing trial: `OBS` on `COM14` → `COM8` heard exactly `['OBS']` → TX=`COM14`, RX=`COM8` (reverse direction untested after success; roles as user set them).
- Smoke: `CLR`×3 → exactly `['CLR']`; `OBS`×3 again → exactly `['OBS']`. SMOKE: PASS, exit 0.
- Proven over the air: TX↔RX packet exchange, OBS/CLR propagation, duplicate suppression (3× repeats → 1 event), RX episode semantics, same-PHY (default S=8 both ends) operation, UART host integration both sides.
- Not covered this run: visual LED confirmation, Button-1 PHY switching over the air (needs coordinated presses on both boards), S=8-vs-1M range comparison, `rx_logger.py` run (script performed the equivalent reads), second-direction pairing.

### Changes made

- None to repo/hardware. Temp: `smoke_test.py`. Link left idling CLR (TX) / CLR-heard (RX).
- Appended this entry. No commits, no pushes.

### Conclusion

- End-to-end control path works: sensing-side UART → TX latch → BLE → RX dedup → robot-side UART, with exact single-event semantics under repeated broadcasts.
- Remaining: human LED/button cross-checks + optional coordinated PHY-switch test + logger run.

### Next boundary

Human: confirm role/PHY LEDs on both boards; coordinated Button-1 presses on both boards followed by re-run of the smoke script to prove over-air PHY switching; optional `rx_logger.py` JSONL run.

## 2026-09-28 — Validation evidence folder created for the commit

### User request

Create a folder inside `firmware/` collecting the test incidents/evidence (packet proof, validation results), so the GitHub commit is complete. Follow-up: corrected a mistaken edit that had deleted the README smoke-test steps (restored verbatim + validation pointers).

### Actions performed

- Created `firmware/validation/` with `README.md` (index, tooling, append-only convention), `2026-09-28-single-board-bringup.md` (nRF52833 correction, flash order, boot proof), `2026-09-28-two-board-smoke-test.md` (procedure, PASS result, exact packet bytes, proven/open items), and `smoke_test.py` (reusable `--tx/--rx` episode test, py_compile-verified, exit 0).
- Repaired `firmware/README.md` smoke-test section after a bad edit (all 8 steps restored; added validation pointers; verified by re-read).
- `git status` check. No hardware access; no commit/push (not instructed).

### Results

- Validation evidence now lives in-repo, dated and self-describing; packet-byte proof preserved in the smoke-test record.
- Working tree ready for commit (all session work uncommitted, as throughout).

### Changes made

- New: `firmware/validation/` (4 files). Modified: `firmware/README.md` (smoke-test section only).
- Appended this entry. No commits, no pushes.

### Conclusion

- Commit content complete from the engineering side; commit/push itself awaits explicit instruction.

### Next boundary

User runs `git commit`/`git push` (or instructs otherwise); then human LED/button cross-checks and optional PHY-switch test.

## 2026-09-28 — Root cleanup: diagnostic clutter moved to debug-evidence/

### User request

Clean up session diagnostic mess folder-wise in the repo root.

### Actions performed

- Moved 13 root files (2 crash dumps, J-Link V9.80 installer, SEGGER logs/reports/JSON, J-Link scripts) plus all 4 `tools/*.ps1` scripts into new `debug-evidence/`; removed the now-empty `tools/`. `MUSE_SESSION_LOG.md` stays at root per session contract.
- Wrote `debug-evidence/README.md` index (contents + old→new path mapping note + pointer to `firmware/validation/` for live evidence).
- Extended `.gitignore` with `*.dmp` and `JLink_Windows_x86_64.exe` (large binaries stay local, small logs/reports/scripts remain committable). No hardware access.

### Results

- Repo root contains only: `build/` (ignored), `debug-evidence/`, `decision-logs/`, `dsp/` (pre-existing, not mine, untouched), `firmware/`, `robotics/`, `session-logs/`, `system/`, `.gitignore`, `MUSE_SESSION_LOG.md`, `README.md`.
- `git status` confirms the move (binaries no longer listed as untracked). Session-log history keeps old root paths truthfully; the README records the relocation.

### Changes made

- New: `debug-evidence/` (13 moved files + README). Modified: `.gitignore`. Deleted: empty `tools/` dir.
- Appended this entry. No commits, no pushes.

### Conclusion

- Tree is organized and commit-ready (modulo the user's commit/push decision); large binaries excluded from the commit by ignore rules.

### Next boundary

User commits/pushes (or instructs); then human LED/button cross-checks.

## 2026-09-28 — Session bundle moved into singular date folder

### User request

Put debug evidence into a singular date folder along with the Muse session.

### Actions performed

- Created root `2026-09-28/`; moved `debug-evidence/` → `2026-09-28/debug-evidence/` and `MUSE_SESSION_LOG.md` → `2026-09-28/MUSE_SESSION_LOG.md` (this file).
- Verified `debug-evidence/README.md`'s `../MUSE_SESSION_LOG.md` link still resolves (now a sibling). No content changes. No hardware access.

### Results

- Root holds only project dirs + `.gitignore` + `README.md`. Session bundle (log + evidence) lives together under `2026-09-28/`. Future entries append to the log at its new path.

### Changes made

- Relocated: `2026-09-28/` (log + evidence). Appended this entry. No commits, no pushes.

### Conclusion

- Requested layout in place; history preserved (old root paths remain truthfully recorded in prior entries).

### Next boundary

User commits/pushes (or instructs); then human LED/button cross-checks.

## 2026-09-28 — nRF52833 image flashed; application provably runs (main loop confirmed)

### User request

Flash once with the corrected `nrf52833dk/nrf52833` image; validate flash/verify, Windows stability, main reached, TX/CLR/S=8 defaults, role + PHY LEDs, Button 1/2 behavior, role-following LEDs, PHY persistence, UART/VCOM, heap-fault elimination; no BLE pair testing; report failures without reflashing; log result.

### Actions performed

- ONE program: `nrfjprog --program build/transceiver/merged.hex --sectorerase --verify` (exit 0, verify OK; UICR untouched by sector erase).
- UICR `0x10001208=0x5A` written AFTER programming + read-back verified; vectors read back `20003EE8/00012E25` (new nrf52833 image values); `nrfjprog --reset` (exit 0).
- T+0 serial capture (port open before reset, 15 s): clean `*** Booting nRF Connect SDK v3.2.3 ***` + Zephyr banner, 99 bytes, NO fault banner.
- Read-only J-Link sessions (`nRF52833_xxAA` device): run-state check (halt/regs/faults/go), GPIO reads ×2 (~1 min apart), main-stack dump (304 words), all exit 0, no unsecure, core resumed each time.
- Host-side symbol mapping (addr2line/nm/objdump) for PC/LR/stack code words. No erase/recover/flash beyond the one program; no memory writes to target (SRAM restore test was prior prompt); Windows stable, no new dumps.

### Results

- Flash command: `nrfjprog --program P:/Github/RIS-Robotics/build/transceiver/merged.hex --sectorerase --verify`. Flash/verify: PASS (exit 0, "Verify successful").
- Windows stability: stable across 6+ probe operations this cycle; boot `10:40:36` unchanged; only the two preserved dumps.
- Boot/runtime: clean boot banner, zero fault registers (CFSR/HFSR/MMFAR/BFAR all zero; DFSR=HALTED only from our halts). Previous `sys_heap_init` BusFault ELIMINATED.
- Execution proof: halted core shows PC `19586` = `arch_cpu_idle` called from `idle` thread, IPSR=0 (thread mode), PSP active — kernel scheduling normally. Main-thread stack (`z_main_stack`) backtrace: `z_thread_entry → … → z_tick_sleep ← z_swap_irqlock`, with `bt_enable` ABSENT from the stack → `main()` started, `bt_enable()` returned, main is cycling in `transceiver_run()`'s `k_sleep(5)`. Combined with GPIO (below), the app runs its main loop.
- Defaults (by code + register state): TX role (boot default, no button press yet), `CLR` latch, Coded S=8 (`led2` driven ON, see GPIO).
- GPIO (P0, active-low, DTS-derived): DIR=`E060` (P0.13/14/15 + UART P0.5/6 as outputs — `leds_init()` executed); OUT=`6060` twice (~1 min apart): bit15 LOW = `led2` ON = S=8 (`phy_indicator_update()` executed); bits 13/14 HIGH (role LEDs off phase at both samples — blink phase not captured by two 60 s-apart samples).
- LED blink / Button 1 / Button 2 / role-following / PHY persistence: NOT remotely observable — require human eyes/hands; requested below. Register evidence is consistent with (but does not alone prove) correct blinking.
- UART/VCOM: `COM8`/`COM9` enumerate; port opens at 115200; 5 s post-boot silence (CORRECT for TX/`CLR`: app prints nothing in this state, and no fault banner exists); `OBS`/`CLR` writes accepted without error.
- Second-board items still blocked: TX↔RX exchange, OBS/CLR propagation, over-air dedup, on-air S=8 link, RX-side UART output, range/reliability, host-test execution.

### Changes made

- Target: transceiver `nrf52833dk` image programmed+verified; UICR `0x5A` (dev-open, stays); board reset into running app. No repo source/config changes.
- Temp: `jlink_run_check.jlink`, `jlink_gpio33.jlink`, `jlink_mainstack.jlink`, `run_check.log`, `gpio33*.log`, `mainstack.log`, `flash1b`? (none). Appended this entry. No commits, no pushes.

### Conclusion

- Corrected image boots cleanly past the previously fatal heap init; kernel schedules; main loop runs; LED GPIOs configured with PHY indication on; UART path healthy and correctly silent.
- The only remaining validations need a human at the bench (LED blink, both buttons) and, afterward, the second board.

### Next boundary

Human confirmation of LED1+LED2 blinking / LED3 solid, then Button-2 (RX: single blink) and Button-1 (LED3 toggles, roles/PHY independent) observations; then second-board over-air validation.

## 2026-09-28 — Session bundle as sessions/2026-09-28/ + investigation README

### User request

Restructure: `sessions/` parent with one folder per date containing everything for that date, plus a README with the full investigation description. (Supersedes the flat root `2026-09-28/` layout.)

### Actions performed

- Moved root `2026-09-28/` → `sessions/2026-09-28/` (`MUSE_SESSION_LOG.md` + `debug-evidence/` intact; evidence README link still resolves).
- Wrote `sessions/2026-09-28/README.md`: 7-part investigation summary (BSOD/stack reset, controlled tests, firmware, governance migration, APPROTECT saga, heap-fault hunt + Case B, corrected build/boot/two-board PASS, open items). Fixed a typo before finishing.
- Wrote `sessions/README.md`: parent convention + index. No hardware access.

### Results

- Layout: `sessions/README.md`, `sessions/2026-09-28/{README.md, MUSE_SESSION_LOG.md, debug-evidence/}`. Root clean. All log entries verified present (see correction entry above).

### Changes made

- New: `sessions/` (moved date bundle + 2 READMEs). Appended this entry. No commits, no pushes.

### Conclusion

- Requested structure in place; future dates accumulate the same way.

### Next boundary

User commits/pushes (or instructs); then human LED/button cross-checks.

## 2026-09-28 — DSP state machines + serial integration design (analysis only, uncommitted)

### User request

Analyze/document (no serial implementation): all explicit/implicit DSP state machines; exact person/robot path; one recommended serial insertion point with file/function/variable/before/after; CLEAR/OBSTACLE adapter FSM + Mermaid; transition-only OBS/CLR semantics; CLR definability; hysteresis eval; placeholder + index-5 + unknown-class handling; failure semantics (never coerce unknown to CLR); NRF TX contract from firmware source; ownership boundary (`dsp/integration/`, not created); exact future call flow; blockers. Update dsp + system docs surgically. Report A–I.

### Actions performed

- Verified NRF TX contract from `firmware/transceiver/src/main.c` (`tx_poll_uart`: exact OBS/CLR lines, 7-char buffer, overlong-discard, invalid-ignored, latch + re-advertise on change only; 115200 8N1 established earlier).
- Created `dsp/docs/state-machines.md` (SM-1 recording FSM, SM-2 window accumulator, SM-3 vote temporal filter — explicitly not FSM/hysteresis, SM-4 clutter memory, SM-5 GUI latch incl. ValueError-on-unknown path, SM-6 NRF latch, proposed SM-7; raw-vs-stable-vs-control separation; terminology verdicts) and `dsp/docs/serial-integration-point.md` (class table incl. producible index 5, predicate, insertion point, 4-way placement analysis, FSM + Mermaid, transition-only rationale, CLR-via-vote with placeholder untrustworthiness stated, no invented timeouts, failure table with hold-not-clear invariant, contract, ownership, call flow, 5 blockers).
- Updated indexes (`dsp/docs/README.md`, `dsp/README.md` map + status row) and cross-links (pipeline vote stage, contracts vote row, real-time failure row, rolling-vote validation note, `system.md` + `control-signal-path.md` planned-chain sentences). No serial code written; `dsp/integration/` not created.
- Validated: links PASS (18 files), TOCs present, diff is docs-only (8 modified + 2 new, +29/−6), no implementation files touched. No commit (not instructed).

### Results

- Insertion point: `dsp/collect_data_realtime.py` → `record_frames()`, after `vote_predictions()` yields `voted_name`, before print/GUI update; adapter `class_to_obstacle_state()` → proposed FSM → future writer.
- Semantics: internal CLEAR/OBSTACLE, wire CLR/OBS on transitions only, init CLEAR (matches NRF boot), unknown/error holds + faults visibly; vote is symmetric (flicker possible, no hysteresis); GUI stays display-only.
- Blockers: no trained model (bridge must stay disabled), undocumented antenna geometry, pyserial undeclarated, no COM discovery, GUI ValueError ordering.

### Changes made

- Created: `dsp/docs/state-machines.md`, `dsp/docs/serial-integration-point.md`. Modified: 8 docs (listed above). No code changes. Uncommitted working tree. Temp: none new.
- Appended this entry. No commits, no pushes.

### Conclusion

- Code-ready integration design complete with exact symbols and explicit blockers; the serial bridge remains correctly unimplemented.

### Next boundary

Human LED/button cross-checks (transceiver); serial implementation as a separately authorized task once blockers (trained model first) lift.

## 2026-09-28 — DSP→NRF serial integration implemented, tested, pushed (no HW)

### User request

Implement the analyzed boundary: ObstacleStateAdapter (CLEAR/OBSTACLE, transition-only, unknown-hold, init CLEAR silent) + SerialStateOutput (exact framing, 115200, retry via last-transmitted, clean close) wired after vote_predictions() before print/GUI; argparse CLI (--serial-port/--baud/--serial-allow-placeholder dev override); placeholder gate refusing serial in normal mode; pyserial declared; docs converted to implementation records; 14 old + new FSM/serial/wiring tests green; hardware smoke only if TX board present; commit + push to main.

### Actions performed

- Created `dsp/integration/` (`obstacle_state.py`, `serial_output.py`, `__init__.py`, `README.md`); mapping derived from `DETECTION_CLASS_NAMES` (0/1 obstacle, 2 clear).
- Wired `collect_data_realtime.py`: argparse, placeholder gate (exit 2), eager open (fail fast), adapter+`sync()` per prediction before print/GUI, `finally` close, `main()` returns int.
- Verified firmware contract from `main.c` (`tx_poll_uart`): exact lines, 7-char buffer, invalid ignored, latch-on-change, boot CLR, 115200.
- Added `pyserial` to `dsp/requirements.txt`; wrote `tests/test_serial_integration.py` (15 tests: FSM table, episode, framing, no-write cases, failure/retry, close, pyserial-absent open failure, CLI defaults, record_frames wiring with fake stream).
- Ran suite with SDK stub: 29/29 PASS (14 pre-existing intact).
- Docs: SM-7 implemented record, serial doc → implementation record (real call flow, CLI, gate, failures), status/table/pointer updates in dsp/README, pipeline, contracts, real-time, rolling-vote, validation (+serial test row), system.md, control-signal-path.md, root README.
- Hardware check: no probes/COMs OK (all Unknown/disconnected) → no smoke test per task rules; stated pending.
- Validated: links PASS (19 files), diff scope (code: integration/ + wiring + requirements + tests; docs as listed; no DSP algorithm changes), then committed + pushed.

### Results

- Control path live in code: vote → adapter latch → transition-only `b"OBS\n"`/`b"CLR\n"` → (future) NRF TX. Placeholder output cannot reach hardware in normal mode (startup refusal); explicit dev override is named, bannered, documented.
- Unknown/invalid holds state + faults visibly, never clears; failures retry via stale `last_transmitted`; shutdown emits nothing and closes quietly.

### Changes made

- Created: `dsp/integration/` (4 files), `dsp/tests/test_serial_integration.py`.
- Modified: `dsp/collect_data_realtime.py` (+62), `dsp/requirements.txt`, 9 docs.
- Commit + push below. No hardware touched.

### Conclusion

- Implementation complete, software-tested, documented; hardware validation pending board availability.

### Next boundary

Human LED/button cross-checks (transceiver); NRF serial smoke test when a TX board is connected; trained detector remains future work.

## 2026-09-28 — DSP subsystem documentation (industry-grade record, committed + pushed)

### User request

Turn new `dsp/` (real-time radar/DSP) into a seriously documented engineering subsystem: architecture fit, pipeline, per-algorithm math/physics, variable↔concept mapping, real-time behavior, parameters, limits/failures, validation evidence, code traceability — all derived from the actual implementation, no invented DSP, no implementation changes. Follow the prescribed hierarchy (dsp/README, docs/×5, algorithms/ each, tests index), update root README + system docs surgically, preserve history, validate everything, commit to main + push.

### Actions performed

- Inspected repo + full `dsp/` tree (4 sources, tests, requirements, existing README, .gitignore); read all source files fully; reviewed root/system/firmware/decision docs conventions; prior commit `01a5329` had already landed `dsp/` + all session work (tree was clean).
- Environment probe: numpy 2.5.2/matplotlib/tkinter present; `ifxradarsdk`, `keras`, model file absent → suite unrunnable as-is.
- Wrote minimal SDK stub (temp, outside repo) and executed the full hardware-free suite: 14/14 PASS in 0.715 s.
- Created 11 docs (`dsp/README.md` rewrite preserving run/placeholder/settings content, `docs/` ×5, `algorithms/` index + 4 algorithm docs, `tests/README.md`); edited root `README.md` (DSP chain line + subsystem bullet) and `system/system.md` + `control-signal-path.md` (DSP in-repo note; serial trigger still pending).
- Validated: link check PASS (16 files), TOCs present, source-vs-doc consistency review, `git diff` shows docs only, `__pycache__` removed; committed `e53fb1b` (+1488/−2, 16 files) and pushed (0/0 with origin).

### Results

- Pipeline discovered: metrics/chirp config → blocking acquisition → DC-remove/BH/range-FFT/Doppler-FFT/clutter-average+MTI/fftshift → antenna-sum + Capon elevation on pair [1, 2] → (32, 256) maps → non-overlapping 10-frame windows → per-frame z-norm → CNN-LSTM (placeholder) → rolling ≤5 vote → GUI/terminal + `.npy` save; azimuth commented out; live-plot diagnostic branch separate.
- Key facts: 3 GHz BW → 0.05 m; λ ≈ 4.94 mm; d=λ/2 steering assumption; clutter weights 0.6/0.4 never reset; single-threaded loop, no drop accounting; no serial/ROS output exists in dsp/ (architecture gap preserved in docs); placeholder mapping + missing CLASS_NAMES[5] + real-part-only live plot + personal save path documented as limitations, not fixed.
- Open gaps recorded: no timing/CPU/accuracy/false-alarm metrics; antenna geometry undocumented; no calibration/ground-truth data; requirements.txt incomplete; model file absent.

### Changes made

- Docs only: 4 modified (root README, system.md, control-signal-path.md, dsp/README rewrite), 12 created. No implementation change (`git diff` clean of code).
- Committed `e53fb1b` to main and pushed to origin (verified 0 ahead/behind, clean tree).

### Conclusion

- DSP is now a first-class documented subsystem with traceable, evidence-graded docs; the serial-trigger integration ask is unchanged and explicitly still open.

### Next boundary

Human LED/button cross-checks (transceiver); trained detector + serial trigger remain sensing-side future work.

## 2026-09-28 — Automatic NRF serial discovery (no manual port, pushed)

### User request

Replace manual `--serial-port` with defensive auto-discovery (pyserial metadata, cross-platform, board grouping, silence-safe, transmit-free); unambiguous-only selection; non-fatal failures; placeholder protection intact; architecture separated; tests incl. app-continuity; docs updated; stale manual-port refs removed; no firmware/DSP-algorithm changes; live Windows metadata check; commit + push main.

### Actions performed

- Searched repo: no existing RSSI/serial-monitor utility exists (only an unrelated Bluetooth note) — implemented from the specified approach.
- Created `dsp/integration/serial_discovery.py` (`find_nrf_boards` grouping by serial→location→HWID→device; candidate tokens j-link/jlink/segger/nrf/nordic/cmsis-dap + SEGGER VID 0x1366; bare "usb serial" deliberately insufficient — generic adapters share it; lowest-interface selection documented from MI_00 lab evidence; never raises/transmits).
- Rewired `collect_data_realtime.py`: removed `--serial-port`; startup discovery with case diagnostics; open-failure downgrade (warn, no exit); placeholder gate preserved; kept `--serial-baud/--serial-allow-placeholder`.
- Added `dsp/tests/test_serial_discovery.py` (12 tests: all required cases) + CLI-defaults test; fixed 2 test bugs of mine (frame-count expectation, duplicate def).
- Restored `session-logs/` (entire directory missing from disk, not by me) via `git checkout` before committing — history preserved, deletion not committed.
- Ran: 41/41 PASS; links PASS (19 files); live `list_ports` → zero ports (Case B, no transmission); diff reviewed; committed + pushed (below).

### Results

- Startup path: enumerate → filter → group → 0 (warn+disabled) / >1 (list+disabled) / 1 board (lowest CDC interface, noted) → placeholder gate → open-or-warn. DSP/GUI/recording never blocked; silence never rejects; no guessing (first/lowest COM explicitly refused).
- Placeholder protection intact (refusal preserved; override still explicit/dev-only).

### Changes made

- Created: `serial_discovery.py`, `test_serial_discovery.py`. Modified: `collect_data_realtime.py`, both READMEs (integration + dsp), serial-integration-point, pipeline, system.md, control-signal-path.md, serial test (CLI). No firmware/algorithm changes.
- Commit + push below. No hardware touched (boards absent).

### Conclusion

- Discovery is convenience-only: any failure degrades to serial-disabled with a clear warning; control can never flow to a guessed port.

### Next boundary

Human LED/button cross-checks; NRF serial smoke test when a TX board reappears; trained detector future work.
