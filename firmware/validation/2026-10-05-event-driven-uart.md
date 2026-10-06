# Validation: 2026-10-05 event-driven UART transport

## Contents

- [Scope](#scope)
- [Build and host checks](#build-and-host-checks)
- [Two-board flash](#two-board-flash)
- [UART endpoint checks](#uart-endpoint-checks)
- [Still open](#still-open)

## Scope

Date: 2026-10-05. Repository base before these changes: `79aae0383d8d4c4d62bac4964c1cedf59015651a`.

This record covers replacing the console/polling UART path with Zephyr's asynchronous UART event API, bounded `OBS`/`CLR` line framing, generated-image build, host protocol checks, and programming both connected nRF52833 DKs. It distinguishes those checks from the not-yet-captured physical RX output path.

## Build and host checks

- Board target: `nrf52833dk/nrf52833`.
- SDK/toolchain: nRF Connect SDK v3.2.3, Zephyr 4.2.99, Zephyr SDK 0.17.0.
- Build: PASS. Flash use: 122040 B / 512 KB. RAM use: 22636 B / 128 KB.
- Image: `firmware/transceiver/build/zephyr/zephyr.hex`.
- Image SHA-256: `A428B7C9D7A89B7DDF6DE186123ACE201A247EDA2B528EFC56234D42DC9E4D0E`.
- Host protocol tests: PASS, 70 checks.
- Generated configuration: `CONFIG_UART_ASYNC_API=y`; `CONFIG_CONSOLE`, `CONFIG_UART_CONSOLE`, and `CONFIG_LOG` are not set. `CONFIG_PRINTK=y` is selected by Kconfig, but no console backend is enabled and the application has no printk output path.

The parser accepts only a complete exact ASCII `OBS` or `CLR` line ending in LF or CRLF. Malformed and overlong lines are discarded through LF. The RX stub modes remain Natural, Forced CLR, and Forced OBS; this build does not treat stub activity as evidence for natural BLE reception.

## Two-board flash

Both boards were programmed and image-verified with explicit probe IDs using `nrfjprog --program <image> --sectorerase --verify --family NRF52 --snr <id>`, then reset:

| Probe ID | VCOM0 / UART0 | Flash result |
|---|---|---|
| `1050670813` | COM8 | PASS — verify successful |
| `1050611489` | COM14 | PASS — verify successful |

The device tree routes the protocol UART through UART0. PnP parent IDs and `nrfjprog --com` associated COM8 with probe `1050670813` and COM14 with probe `1050611489`. Both were confirmed as SEGGER J-Link VCOM0 endpoints. The existing UICR contents were preserved by sector erase.

An initial programming attempt omitted `--sectorerase`; verification failed at address `0x00000001`. Repeating the program operation with the repository's documented sector-erase procedure completed verification successfully on each board.

## UART endpoint checks

After reset, COM8 and COM14 each opened at 115200 8N1 and accepted host writes containing complete `OBS` and `CLR` records. Neither returned bytes while its board was in the boot TX role. That silence is expected for TX and does not establish that commands changed the state or that RX emitted events.

## Still open

- Switch one board to RX with physical Button 2, send `OBS` then `CLR` from the other board over UART0, and capture both complete lines on the RX VCOM. This is required before reporting complete physical serial delivery.
- Validate the two-board natural BLE path on this image and record its captured RX output.
- Observe the current image's RX stub LED sequence on hardware if revalidation is required; the existing stub evidence predates this UART change.
