# RIS Transceiver

> **Hardware correction (2026-09-28):** the connected development board was previously documented as a Nordic nRF52840 DK, but FICR identification proves the physical MCU is an **nRF52833** (128 KB RAM / 512 KB flash). The canonical build target is therefore the Nordic nRF52833 DK. Images built for `nrf52840dk` overrun physical SRAM and BusFault before `main()`; see `ble-runtime-0004` and the session log. The nRF52833 DK provides the same `led0`/`led1`/`led2`/`sw0`/`sw1` aliases and console, so no firmware source change was required.

The **Transceiver** is one nRF Connect SDK/Zephyr application built as a **single firmware image**. The same binary performs either side of the `OBS`/`CLR` protocol: TX and RX are **runtime roles** selected on-device with a physical button (`ble-runtime-0004`). There are no separate TX/RX images and no build-time role selection.

## Supported setup

The current, verified build target is the Nordic nRF52833 DK:

- board target: `nrf52833dk/nrf52833`
- MCU: nRF52833 (128 KB SRAM `0x20000000–0x2001FFFF`, 512 KB flash)
- SDK: nRF Connect SDK v3.2.3
- build/flash tool: `west`
- console: the board's Zephyr console at 115200 baud, 8 data bits, no parity, 1 stop bit

The firmware uses the selected board's devicetree LED and button aliases. No GPIO pin numbers are embedded in the application. Role indication needs `led0` and `led1`; PHY indication needs `led2`. Role/PHY switching needs `sw0` (Button 1, PHY switch) and `sw1` (Button 2, role switch).

If the physical boards are not nRF52833 DKs, select their actual Zephyr board target and first confirm that it supplies the required aliases (`led0`, `led1`, `led2`, `sw0`, `sw1`) and supports extended advertising, LE Coded PHY, and advertising coding selection. (A previous revision of this file named the nRF52840 DK here; that was the misidentified hardware, corrected 2026-09-28.)

## Layout

```text
firmware/
├── README.md
├── transceiver/
│   ├── CMakeLists.txt
│   ├── Kconfig           blink-interval option (no role selection)
│   ├── prj.conf       shared hardware/Bluetooth configuration
│   ├── src/main.c     application: runtime roles, BLE, buttons, LEDs
│   ├── src/protocol.h pure OBS/CLR + role/PHY state-machine helpers (firmware + host test)
│   └── tests/test_protocol.c host-side unit test for protocol.h
└── tools/
    ├── requirements.txt
    └── rx_logger.py
```

## Runtime roles

A freshly booted board starts as **TX + LE Coded S=8**. Pressing Button 2 (`sw1` alias, 200 ms debounce) toggles the operating role at runtime: TX ↔ RX. Role and PHY are independent dimensions — switching role preserves the current PHY and switching PHY preserves the current role, so all four combinations (TX/RX × S=8/1M) are reachable. There is no role persistence: every boot starts as TX + Coded S=8. No reboot or reflash is needed to change role.

### Entering RX (TX → RX)

1. Advertising is stopped and the advertiser deleted.
2. Partial UART input is discarded.
3. The RX deduplication state is initialized to unknown (fresh observation epoch).
4. Scanning starts on the currently selected PHY.
5. Only if scanning starts does RX become the active role: `led1` is forced off so only one role LED blinks.

### Entering TX (RX → TX)

1. Scanning is stopped.
2. RX transient state is cleared.
3. The TX latch is deliberately re-initialized to `CLR` and the UART is flushed so stale bytes can never become a command.
4. Advertising of `CLR` starts on the currently selected PHY.
5. Only if advertising starts does TX become the active role and both role LEDs resume blinking.

A button press only requests a role; the requested role becomes active solely on successful transport start. If the new side fails to start, the firmware emits a rare diagnostic line (`ERR scan-start <err>` / `ERR adv-start <err>`) and attempts to restore the previous side. If the restore succeeds, the previous role simply remains active with its normal indication. If both sides are down, the role LEDs are forced off and blinking is suspended — never a normal TX/RX pattern — while the `led2` PHY indicator is unaffected; pressing Button 2 again retries.

### TX role

TX blinks the board-defined `led0` and `led1`. UART input is interpreted as host control commands only in TX mode. It reads newline-delimited commands from the serial console:

- `OBS` latches the state to obstacle;
- `CLR` latches the state to clear.

The current state is continuously present in non-connectable BLE extended advertisements. Repeating `OBS` or `CLR` does not change the state. Only the exact strings `OBS` and `CLR` act; anything else (wrong case, padding, overlong lines) is explicitly ignored and never coerced into a state. Pressing Button 1 switches the BLE PHY mode (see below); the latched `OBS`/`CLR` state is preserved across the switch and re-advertised on the new PHY.

### RX role

RX blinks only the board-defined `led0` and never consumes incoming serial bytes as commands. It passively scans on the selected PHY (Coded S=8 by default) and recognizes the Transceiver's service-data UUID. It emits only the first transition in each obstacle episode:

```text
wireless: OBS OBS OBS OBS CLR CLR CLR OBS OBS
serial:   OBS             CLR         OBS
```

An initial clear advertisement is intentionally silent. RX emits `CLR` only after it has emitted an `OBS`.

Pressing Button 1 switches the BLE PHY mode (see below). A PHY switch starts a new RX observation epoch: the deduplication state resets to unknown, so stale state from the previous PHY is never re-emitted. The first packet heard on the new PHY behaves like a fresh boot (initial `CLR` silent, first `OBS` emitted).

## BLE PHY modes: LE 1M and LE Coded S=8

Both roles support two PHY modes (`ble-runtime-0004`; PHY details from `ble-runtime-0003`):

| Mode | TX advertising | RX scanning |
|---|---|---|
| LE Coded S=8 (default) | Extended advertising with `BT_LE_ADV_OPT_CODED` + `BT_LE_ADV_OPT_REQUIRE_S8_CODING` | `BT_LE_SCAN_OPT_CODED \| BT_LE_SCAN_OPT_NO_1M` (coded only) |
| LE 1M | Extended advertising, default 1M PHY (no coded options) | No coded/scan-only options (1M only) |

Coded PHY uses the long-range S=8 configuration explicitly: `prj.conf` enables `CONFIG_BT_EXT_ADV_CODING_SELECTION`, and TX combines it with the coded + require-S8 advertising options. In this SDK that combination uses the extended-advertising-parameters-v2 coding-selection field to require S=8 for primary and secondary coded advertising. There is no silent fallback to S=2 in the TX path: the mode is either explicit S=8 advertising or explicit 1M advertising.

### PHY switching with Button 1

Pressing the board's Button 1 (`sw0` alias, 200 ms debounce) toggles the PHY mode at runtime in either role. TX tears down and recreates its advertiser on the new PHY with the preserved latched state; RX restarts its scan on the new PHY and resets its deduplication epoch. If a restart fails, TX falls back to the previous PHY when possible and the firmware emits a rare diagnostic line (`ERR adv-restart`, `ERR scan-restart`) on the console; hosts must ignore console lines other than `OBS`/`CLR`.

### Role switching with Button 2

Pressing the board's Button 2 (`sw1` alias, 200 ms debounce) toggles the TX/RX role at runtime as described above. Do not confuse the two buttons: Button 1 changes PHY, Button 2 changes role, and neither channel interferes with the other.

### LED indication

Role indication is continuous: TX blinks `led0` + `led1` (two LEDs), RX blinks `led0` (one LED), always reflecting the current runtime role. PHY mode is shown separately on `led2` so role indication is never disturbed: `led2` on = LE Coded S=8, `led2` off = LE 1M. Role and PHY are therefore both readable without a debugger.

## Build and flash

Run this command from the repository root in an nRF Connect SDK v3.2.3 terminal. There is one build producing one image for both roles:

```powershell
west build -p always -b nrf52833dk/nrf52833 firmware/transceiver -d build/transceiver
west flash -d build/transceiver
```

A freshly flashed board boots as TX (two LEDs blink, `led2` on for Coded S=8). Press Button 2 to switch it to RX (one LED blinks); press Button 1 on either board to switch its PHY. In TX mode the serial port accepts `OBS` and `CLR`, each followed by Enter/newline.

If more than one debugger is connected, pass the probe identifier supported by the runner, for example `west flash -d build/transceiver --dev-id <serial-number>`.

## RX Python logger

Install the one host dependency:

```powershell
python -m pip install -r firmware/tools/requirements.txt
```

Run the logger with an explicit serial device and optional JSON Lines output file:

```powershell
python firmware/tools/rx_logger.py --port COM5 --baud 115200 --output transceiver-events.jsonl
```

Linux example: replace `COM5` with `/dev/ttyACM0`. The logger prints and, when `--output` is supplied, appends records such as:

```json
{"event":"OBS","received_at":"2026-09-16T23:18:42.125+00:00"}
{"event":"CLR","received_at":"2026-09-16T23:18:49.602+00:00"}
```

Timestamps are generated by the RX-side host in UTC when a complete serial event is received.

## `OBS` → `CLR` smoke test (requires both boards)

1. Flash the single image on both boards. Both boot as TX (two LEDs blink, `led2` on).
2. Press Button 2 on one board to switch it to RX; verify one LED blinks.
3. Start `rx_logger.py` on the RX serial port.
4. Open the TX serial port at 115200 8N1 with a line ending enabled.
5. Send `OBS` several times. The logger must produce exactly one `OBS` record.
6. Send `CLR` several times. The logger must produce exactly one following `CLR` record.
7. Send `OBS` again. The logger must produce one new `OBS` record.
8. Press Button 2 on each board to swap roles and repeat: role switching must not require reflashing.

Do not open the same serial port in both the logger and another terminal simultaneously.

Validated 2026-09-28 — see [`validation/2026-09-28-two-board-smoke-test.md`](validation/2026-09-28-two-board-smoke-test.md) (PASS) and the reusable [`validation/smoke_test.py`](validation/smoke_test.py). Dated evidence lives in [`validation/`](validation/).

## System boundary

This directory implements only:

```text
Radar -> serial -> TX Transceiver -> BLE (LE 1M or Coded PHY S=8)
      -> RX Transceiver -> serial -> Python logger
```

SSH forwarding, ROS arbitration, and Jackal `cmd_vel` control are downstream context and are intentionally not implemented here.

## Validation status (2026-09-28): BUILD ONLY, NO FLASH

One image builds for `nrf52833dk/nrf52833` (NCS v3.2.3, `ble-runtime-0004`):

```powershell
west build -p always -b nrf52833dk/nrf52833 firmware/transceiver -d build/transceiver
```

Outside an NCS terminal, set `ZEPHYR_BASE=C:/ncs/v3.2.3/zephyr`, `ZEPHYR_TOOLCHAIN_VARIANT=zephyr`, `ZEPHYR_SDK_INSTALL_DIR=<toolchain>/opt/zephyr-sdk`, extend `PATH` with the toolchain `opt/bin` and `mingw64/bin` (git) directories, and pass `-z C:/ncs/v3.2.3/zephyr` to `west`. No `EXTRA_CONF_FILE` role selection exists anymore.

Verified without hardware: the single image links (`build/transceiver/transceiver/zephyr/zephyr.hex` 326104 B, `.elf`, `merged.hex` 326048 B; FLASH 115916 B / 22.11 % of 512 KB, RAM 21988 B / 16.78 % of 128 KB), generated `.config` confirms `CONFIG_SOC_NRF52833` / board `nrf52833dk/nrf52833` with `CONFIG_BT` + broadcaster + observer, `CONFIG_GPIO`, `CONFIG_SERIAL`/`UART_CONSOLE`, coded-PHY and coding-selection support, blink interval, and no remaining `TRANSCEIVER_ROLE_*` options. Heap verification from the ELF: `_end`=`0x200055E4`, aligned base `0x200055E8`, size `0x1AA18`, end exactly `0x20020000` — no address exceeds physical SRAM end `0x2001FFFF`. The linked binary contains both the TX advertise path and the RX scan path. `tests/test_protocol.c` was compile-checked only — with the Zephyr SDK ARM cross-compiler (`arm-zephyr-eabi-gcc` 12.2.0, `-c -Wall -Wextra -std=c99`, exit 0, no warnings) producing an object file; it was never linked or executed, and no host-targeted C compiler (gcc/cl/clang) exists on this machine — so the vectors remain validated by inspection against `src/protocol.h` until the test can run on a host with a compiler.

No board was flashed, erased, recovered, or connected to during this development.

Still requires two physical nRF52833 DKs: same-image TX ↔ RX packet exchange, `OBS`/`CLR` propagation, duplicate suppression over the air, Button-2 role switching and Button-1 PHY switching on real hardware, LE Coded S=8 operation over the real radio link, UART host integration in both roles, LED behavior on hardware, and range/reliability characterization.
