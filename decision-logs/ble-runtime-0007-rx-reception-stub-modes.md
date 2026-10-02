# Decision: RX Reception Stub Modes

**ID:** `ble-runtime-0007`  
**Previous ID:** None  
**Status:** Accepted — RX testing input and mode indication  
**Date:** 2026-10-02  
**Scope:** RX receive-path stubbing for board-level tests

## Decision

Button 3 (`sw2`) controls RX reception mode while the Transceiver is in the RX role. It cycles through three states:

1. **Natural** — process valid over-the-air Transceiver packets as usual.
2. **Forced CLR** — ignore natural packets and synthesize a valid CLR reception every 500 ms.
3. **Forced OBS** — ignore natural packets and synthesize a valid OBS reception every 500 ms.

The next Button 3 press after Forced OBS returns to Natural. Entering RX starts in Natural. Leaving RX discards the selected stub mode; re-entering RX starts in Natural. Button 3 keeps its existing TX behavior while TX is active.

Natural and synthetic states use the same RX state-processing and duplicate-suppression path. Each valid natural or synthetic receive event requests the usual RX activity pulse on physical LED2 (Zephyr alias `led1`); the serial state output continues to emit only when the received state changes. During either forced mode, natural packets are ignored and cannot change the reported state.

Physical LED4 (Zephyr alias `led3`) indicates the selected RX mode:

- off in Natural;
- steady on in Forced CLR;
- blinks at 1 Hz in Forced OBS.

The existing RX role indication on physical LED1 (`led0`), RX event pulse on physical LED2 (`led1`), and PHY indication on physical LED3 (`led2`) retain their meanings. Physical LED4 is required for this mode indication. LED4 is off outside the RX role.

## Rationale

The stub modes let one board exercise the receiver’s state processing, duplicate suppression, serial output, and event LED without a second transmitter. Explicit mode indication makes it clear when received data is synthetic. Ignoring natural packets during a forced mode prevents real and synthetic states from racing or making the test result ambiguous.

## Consequences

- The selected board must provide the `led3` alias in addition to the existing LED and button aliases.
- Button 3 has role-specific behavior: it toggles TX state in TX and cycles RX stub modes in RX.
- The stub is a receive-side test source only; it does not start advertising or modify TX state.
- Board testing should verify the three-step mode cycle, LED4 mode patterns, LED2 receive pulses, synthetic `CLR`/`OBS` output, and suppression of over-the-air packets while forced.
