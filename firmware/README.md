# RIS Transceiver

> **Hardware correction (2026-09-28):** the connected development board was previously documented as a Nordic nRF52840 DK, but FICR identification proves the physical MCU is an **nRF52833** (128 KB RAM / 512 KB flash). The canonical build target is therefore the Nordic nRF52833 DK. Images built for `nrf52840dk` overrun physical SRAM and BusFault before `main()`; see `ble-runtime-0004` and the session log. The nRF52833 DK provides the required `led0` through `led3` and `sw0` through `sw2` aliases and console.

The **Transceiver** is one nRF Connect SDK/Zephyr application built as a **single firmware image**. The same binary performs either side of the `OBS`/`CLR` protocol: TX and RX are **runtime roles** selected on-device with a physical button (`ble-runtime-0004`). There are no separate TX/RX images and no build-time role selection.


## Documentation authority

This README owns firmware build, flash, runtime controls, and implementation-specific behavior. Canonical cross-system knowledge lives under [`../docs/`](../docs/):

- transport architecture: [`../docs/architecture/subsystems/wireless-transport.md`](../docs/architecture/subsystems/wireless-transport.md)
- transport features/stubs: [`../docs/features/transport/`](../docs/features/transport/)
- system interfaces: [`../docs/architecture/interactions/interfaces.md`](../docs/architecture/interactions/interfaces.md)
- decisions: [`../docs/decisions/`](../docs/decisions/)
- validation synthesis: [`../docs/validation/`](../docs/validation/)

Raw dated hardware evidence remains in `firmware/validation/`.


## Supported setup

The current, verified build target is the Nordic nRF52833 DK:

- board target: `nrf52833dk/nrf52833`
- MCU: nRF52833 (128 KB SRAM `0x20000000–0x2001FFFF`, 512 KB flash)
- SDK: nRF Connect SDK v3.2.3
- build/flash tool: `west`
- console: the board's Zephyr console at 115200 baud, 8 data bits, no parity, 1 stop bit

The firmware uses the selected board's devicetree LED and button aliases. No GPIO pin numbers are embedded in the application. On the nRF52833 DK, Zephyr aliases `led0` through `led3` map to physical LED1 through LED4. `sw0`, `sw1`, and `sw2` map to Buttons 1, 2, and 3; Button 4 is unused.

If the physical boards are not nRF52833 DKs, select their actual Zephyr board target and first confirm that it supplies the required aliases (`led0` through `led3` and `sw0` through `sw2`) and supports extended advertising, LE Coded PHY, and advertising coding selection.

## Layout

Every immediate child directory is listed below. A child that owns further subdirectories has its own README and continues the navigation recursively.

| Directory | Responsibility | What belongs there | Recursive index |
|---|---|---|---|
| [`transceiver/`](transceiver/) | Shared embedded application | Zephyr build/configuration, runtime TX/RX + PHY behavior, protocol helpers, and host-side protocol tests | [`transceiver/README.md`](transceiver/README.md) |
| [`tools/`](tools/) | Host-side utilities | RX serial logger and its Python dependency list | Leaf directory |
| [`validation/`](validation/) | Firmware-specific hardware evidence | Dated bring-up/smoke-test records and reusable smoke-test utility | [`validation/README.md`](validation/README.md) |

```text
firmware/
├── README.md
├── state-machines.md
├── transceiver/
│   ├── README.md        recursive implementation index
│   ├── CMakeLists.txt
│   ├── Kconfig          TX blink and RX stub intervals (no role selection)
│   ├── prj.conf         shared hardware/Bluetooth configuration
│   ├── src/
│   │   ├── main.c       application: runtime roles, BLE, buttons, LEDs
│   │   └── protocol.h   pure OBS/CLR + role/PHY state-machine helpers
│   └── tests/
│       └── test_protocol.c host-side unit test for protocol.h
├── tools/
│   ├── requirements.txt
│   └── rx_logger.py
└── validation/
    ├── README.md
    ├── smoke_test.py
    └── dated hardware-validation records
```

## Runtime roles

See [Transceiver firmware state machines](state-machines.md) for the detailed TX state and RX receive-source transitions.

Button 3 is role-specific: it toggles `CLR`/`OBS` in TX, and in RX it cycles **Natural → Forced CLR → Forced OBS → Natural**. Forced RX modes ignore real Transceiver packets and inject the selected state at the configured interval (500 ms by default) through the normal RX deduplication/output path. LED4 (`led3`) is off in Natural, steady on in Forced CLR, and blinks at 1 Hz in Forced OBS; LED2 (`led1`) pulses for each accepted synthetic receive event. RX starts in Natural each time the role is entered.

A freshly booted board starts as **TX + LE Coded S=8 + CLR**. Pressing Button 2 (`sw1` alias, 200 ms debounce) toggles the operating role at runtime: TX ↔ RX. Button 3 (`sw2`, 200 ms debounce) toggles TX state in TX role and cycles RX receive source in RX role. Button 1 switches the PHY. Role and PHY are independent dimensions — switching role preserves the current PHY and switching PHY preserves the current role, so all four combinations (TX/RX × S=8/1M) are reachable. There is no role persistence: every boot starts as TX + Coded S=8 + CLR. No reboot or reflash is needed to change role, PHY, or the TX state.

### Entering RX (TX → RX)

1. Advertising is stopped and the advertiser deleted.
2. Partial UART input is discarded.
3. The RX deduplication state is initialized to unknown (fresh observation epoch).
4. Scanning starts on the currently selected PHY.
5. Only if scanning starts does RX become the active role: `led0` stays on for RX role indication; `led1` pulses on valid received packets.

### Entering TX (RX → TX)

1. Scanning is stopped.
2. RX transient state is cleared.
3. The TX latch is deliberately re-initialized to `CLR` and the UART is flushed so stale bytes can never become a command.
4. Advertising of `CLR` starts on the currently selected PHY.
5. Only if advertising starts does TX become the active role: physical LED2 (`led1` alias) stays on for TX role indication. Physical LED1 (`led0` alias) stays off for `CLR` and blinks while `OBS` is advertised.

A button press only requests a role; the requested role becomes active solely on successful transport start. If the new side fails to start, the firmware emits a rare diagnostic line (`ERR scan-start <err>` / `ERR adv-start <err>`) and attempts to restore the previous side. If the restore succeeds, the previous role simply remains active with its normal role and activity indications. If both sides are down, the role and activity LEDs are forced off while the `led2` PHY indicator is unaffected; pressing Button 2 again retries.

### TX role

TX holds physical LED2 (`led1` alias) on as the role indicator. Physical LED1 (`led0` alias) is off while the shared TX state is `CLR` and blinks while it is `OBS`. The blink lasts 80 ms at the configured interval (500 ms by default). UART input is interpreted as host control commands only in TX mode. It reads newline-delimited commands from the serial console:

- `OBS` latches the state to obstacle;
- `CLR` latches the state to clear.

The current state is continuously present in non-connectable BLE extended advertisements. Exact serial lines `OBS` and `CLR` write the shared TX state; Button 3 toggles that same state for local testing. Whichever input writes last determines the state that TX advertises. Repeating the current state does not change it. Wrong case, padding, overlong lines, and other invalid input are ignored. Pressing Button 1 switches the BLE PHY mode (see below); the shared `OBS`/`CLR` state is preserved across the switch and re-advertised on the new PHY. In RX mode, Button 3 cycles the receive source through Natural, Forced CLR, and Forced OBS.

### RX role

RX holds `led0` on as the role indicator and pulses `led1` whenever a valid Transceiver service-data packet is received; repeated packets pulse even when deduplication suppresses a serial event. RX never consumes incoming serial bytes as commands. It passively scans on the selected PHY (Coded S=8 by default) and recognizes the Transceiver's service-data UUID. It emits only the first transition in each obstacle episode:

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

Pressing Button 2 (`sw1`, 200 ms debounce) toggles the TX/RX role. Button 3 (`sw2`, 200 ms debounce) toggles TX state in TX role and cycles the RX receive source in RX role. Button 1 (`sw0`) changes PHY. These controls are independent.

### LED indication

On TX, physical LED2 (`led1` alias) indicates the role; physical LED1 (`led0` alias) is off for `CLR` and blinks for `OBS`. On RX, physical LED1 is the role indicator and physical LED2 pulses on each valid received packet, including duplicates. Physical LED3 (`led2` alias) shows the PHY: on = LE Coded S=8, off = LE 1M. See [`ble-runtime-0006`](../docs/decisions/ble-runtime-0006-shared-tx-state-and-obstacle-indication.md).

## Build and flash

Run this command from the repository root in an nRF Connect SDK v3.2.3 terminal. There is one build producing one image for both roles:

```powershell
west build -p always -b nrf52833dk/nrf52833 firmware/transceiver -d build/transceiver
west flash -d build/transceiver
```

A freshly flashed board boots as TX + CLR (physical LED2 and LED3 on; LED1 and LED4 off). Press Button 3 in TX to toggle to OBS (LED1 blinks), or send `OBS` over TX serial for the same state. Button 2 switches to RX; Button 3 then cycles the RX receive source. Button 1 switches PHY.

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

1. Flash the single image on both boards. Both boot as TX (`led1` on, `led0` pulsing, `led2` on).
2. Press Button 2 on one board to switch it to RX (`led0` on, `led1` pulsing on valid packets).
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
Upstream DSP host -> serial -> TX Transceiver -> BLE (LE 1M or Coded PHY S=8)
                  -> RX Transceiver -> serial -> Python logger
```

SSH forwarding, ROS arbitration, and Jackal `cmd_vel` control are downstream context and are intentionally not implemented here.

## Validation status — 2026-10-02

The earlier build-only state has been superseded by physical bring-up and a two-board smoke test.

### Current build check — 2026-10-02

The RX stub implementation built for `nrf52833dk/nrf52833` with NCS v3.2.3 and was programmed and verified on probe `1050670813`. The resulting image uses 117564 B of flash (22.42% of 512 KB) and 22052 B of RAM (16.82% of 128 KB). The RX stub mode LED patterns were observed on the board.

### Proven on hardware

- Two physical boards were identified by FICR as **nRF52833** and programmed with the single `nrf52833dk/nrf52833` image.
- Correct-target boot was observed without the earlier wrong-target pre-main heap BusFault.
- The two-board default Coded S=8 path passed: repeated `OBS` produced one RX `OBS`, repeated `CLR` produced one RX `CLR`, and a later obstacle episode produced one new RX `OBS`.
- UART host integration on both sides and RX duplicate suppression were exercised in that smoke test.
- The shared TX state and LED1 behavior passed on the connected nRF52833 DK: reset booted to CLR with LED1 off; serial `OBS` and Button 3 both set OBS and blinked LED1; serial `CLR` cleared OBS (including after Button 3 set it), turning LED1 off.
- RX stub LEDs passed on the flashed build: TX boot pattern, RX Natural, Forced CLR, Forced OBS, and return to Natural all matched the expected LED1–LED4 patterns.

Evidence:

- [`validation/2026-09-28-single-board-bringup.md`](validation/2026-09-28-single-board-bringup.md)
- [`validation/2026-09-28-two-board-smoke-test.md`](validation/2026-09-28-two-board-smoke-test.md)
- [`validation/2026-10-02-shared-tx-state-led-test.md`](validation/2026-10-02-shared-tx-state-led-test.md)
- [`validation/2026-10-02-rx-stub-mode-test.md`](validation/2026-10-02-rx-stub-mode-test.md)

### Still open

- natural over-the-air RX packet pulses and suppression of real packets while a stub mode is forced;
- complete RX serial-output check for synthetic `CLR`/`OBS`;
- Button-2 RX-to-TX transition and LE 1M PHY confirmation;
- coordinated Button-1 S=8 <-> 1M over-air switching;
- `rx_logger.py` JSONL run on the physical RX side;
- range/reliability characterization and longer-run behavior;
- host execution of `tests/test_protocol.c` on a machine with a host C compiler.

Firmware validation stops at the transport boundary. DSP-driven TX input, SSH forwarding, ROS arbitration, and Jackal motion control are system-integration work documented under [`../docs/architecture/`](../docs/architecture/).