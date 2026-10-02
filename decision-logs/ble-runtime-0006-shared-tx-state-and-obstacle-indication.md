# Decision: Shared TX State Input and Obstacle Indication

**ID:** `ble-runtime-0006`
**Previous ID:** None
**Status:** Accepted — current TX state input and indicator
**Date:** 2026-10-02
**Scope:** TX state ownership, manual test input, and TX state LED
**Supersedes:** TX activity semantics in `ble-runtime-0005`; its RX packet-reception indication remains in force.

## Decision

The TX state is one shared runtime variable, initialized to `CLR` at boot and when entering TX. Both input methods write that same state:

- newline-delimited serial `OBS` sets the shared state to obstacle;
- newline-delimited serial `CLR` sets it to clear;
- Button 3 (`sw2`) toggles the shared state between clear and obstacle while TX is active.

Both inputs remain available. Each accepted write updates the TX latch and the advertised BLE state; the latest write to the shared state determines what TX advertises. Button 1 continues to change PHY and Button 2 continues to change role.

Physical LED1 (Zephyr alias `led0`) is an obstacle indication on TX: it stays off while the shared state is `CLR`, and blinks while `OBS` is the advertised state. The pulse is 80 ms every `CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS` (500 ms by default). TX role and PHY indications remain on physical LED2 and LED3, respectively. In RX role, LED1 remains the steady role indicator and LED2 pulses on valid received packets, as decided in `ble-runtime-0005`.

## Rationale

The default clear transmission should not look like an alert. Blinking LED1 only during an obstacle episode makes the visible signal follow the semantic `OBS` state. Button 3 provides a local way to create and clear an obstacle episode for testing without sending serial commands, while leaving the serial interface available for normal upstream control.

## Consequences

- The board must provide `sw2` in addition to the existing LED and button aliases.
- The TX serial protocol remains newline-delimited exact `OBS`/`CLR`; the button is an additional input to the same TX state.
- RX reception pulses remain packet-driven and independent of RX serial deduplication.
- Hardware validation should confirm startup `CLR` leaves physical LED1 off, both button and serial inputs update the same advertised state, and either input can clear an obstacle set by the other.
