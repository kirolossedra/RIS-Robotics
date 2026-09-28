# Validation: 2026-09-28 two-board TX → BLE → RX smoke test

Date: 2026-09-28.
Boards: two nRF52833 DKs (J-Link S/N `1050670813` + `1050611489`), both
flashed with the single `nrf52833dk/nrf52833` transceiver image
(`ble-runtime-0004`). Board A left in TX role; board B switched to RX
with Button 2. Both on default Coded S=8 PHY.

## Procedure

1. Enumerated both probes and resolved each board's live MI_00 VCOM
   console (Windows COM numbers shift on re-enumeration; MI_00 is the
   target `uart0`, 115200 8N1).
2. Trial: `OBS` on one console, listen on the other — the answering
   direction identifies TX vs RX (RX ignores serial input).
3. Episode check with flushed buffers between phases:
   `OBS`×3 → expect exactly one `OBS`;
   `CLR`×3 → exactly one `CLR`;
   `OBS`×3 → exactly one new `OBS`.
4. Restored `CLR` so the link idles clear.

Runnable form: `firmware/validation/smoke_test.py --tx <TXPORT> --rx <RXPORT>`.

## Observed result (PASS, first attempt)

- TX = `COM14`, RX = `COM8`.
- `OBS` on TX → RX heard exactly `['OBS']`.
- `CLR` ×3 → exactly `['CLR']`.
- `OBS` ×3 again → exactly `['OBS']`.

## Packet format (as transmitted)

One Service Data AD field per extended advertisement, built in
`firmware/transceiver/src/main.c` (`service_data[18]`, `BT_DATA_SVC_DATA128`):

```text
13 16 116EBBA4DC43C8A9E64E1F521DF9B47B 01 <00|01>
│  │  └──────── 16-byte UUID ─────────┘  │  └ state: 00=CLR, 01=OBS
│  │                                     └ version: always 01
│  └ AD type 0x16 = Service Data, 128-bit UUID
└ AD length 0x13 = 19 bytes follow
```

UUID bytes read canonically as
`7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11` (Bluetooth numeric order).
RX emits only after all checks pass: AD type Service-Data-128,
length exactly 18, full 16-byte UUID match, version `01` — then the
state byte enters dedup. No sniffer was in the loop, so no raw
air-capture file exists; acceptance itself is byte-exact proof
(any mismatch stays silent).

## Proven

TX↔RX packet exchange, OBS/CLR propagation, duplicate suppression
under 3× repeats, RX episode semantics, same-PHY (S=8) operation,
UART host integration on both sides.

## Still open at the time

Visual LED confirmation, coordinated Button-1 PHY switching over the
air, S=8-vs-1M range comparison, `rx_logger.py` JSONL run.
