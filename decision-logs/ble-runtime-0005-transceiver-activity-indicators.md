# Decision: Transceiver Role and Radio Activity Indicators

**ID:** `ble-runtime-0005`
**Previous ID:** None
**Status:** Accepted — current LED behavior
**Date:** 2026-10-02
**Scope:** Transceiver role and BLE radio activity LEDs
**Supersedes:** The LED indication clauses of `ble-runtime-0004`; runtime roles, boot behavior, and PHY selection remain unchanged.

## Decision

The Transceiver LEDs must show both the active role and radio activity. Role indication uses a steady LED, and a separate LED pulses for radio activity:

- **TX role:** `led1` stays on while TX advertising is active. `led0` gives an 80 ms pulse every `CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS` (500 ms by default) while the advertiser is running, indicating ongoing transmissions.
- **RX role:** `led0` stays on while RX scanning is active. `led1` gives an 80 ms pulse whenever a valid Transceiver service-data packet is received, including repeated packets with an unchanged state.
- **PHY:** `led2` remains on for LE Coded S=8 and off for LE 1M.
- If neither transport is active after a start or restore failure, the role and activity LEDs remain off. The PHY indication remains independent.

The role LEDs therefore no longer blink together as the sole role signal. TX and RX activity have distinct indicators, while the steady role LED continues to show which side is active.

## Rationale

Knowing that a board is configured as TX or RX does not show whether its radio path is active. A separate activity pulse provides a visible indication that the TX advertiser is running and confirms packet reception on RX, while preserving an at-a-glance role indication.

TX advertising is continuous, so its LED uses a recurring pulse while the advertiser is enabled. RX activity is driven by received valid Transceiver packets rather than by state transitions, so duplicate advertisements also produce a pulse even though they do not produce another serial event.

## Consequences

- The board continues to require `led0`, `led1`, and `led2` aliases.
- TX's `led0` activity pulse is periodic while advertising is active; RX's `led1` pulse is event-driven by a packet with the Transceiver UUID, protocol version, and a recognized `OBS`/`CLR` state.
- The PHY LED and all button, role, boot, and wire-protocol behavior from `ble-runtime-0004` remain unchanged.
- Physical validation should confirm visibility of the TX pulse, RX packet pulses, steady role indication, and independent PHY indication on the target boards.
