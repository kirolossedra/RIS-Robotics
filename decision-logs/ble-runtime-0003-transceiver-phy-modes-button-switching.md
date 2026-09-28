# Decision: Transceiver BLE PHY Modes with Button Switching

**ID:** `ble-runtime-0003`
**Previous ID:** `DL-007`
**Status:** Superseded by `ble-runtime-0004` (2026-09-28).
**Date:** 2026-09-28
**Scope:** BLE PHY support and runtime PHY selection for the shared Transceiver firmware
**Supersedes (in part):** `ble-runtime-0002` § BLE PHY ("LE Coded PHY only")

> **Historical note:** This record is preserved unchanged below for traceability. Its PHY technical content (explicit S=8, 1M mode, Button-1 switching, `led2` indication, epoch reset, `ERR` diagnostics) remains valid and is incorporated into `ble-runtime-0004`. The statements assuming build-time TX/RX roles ("unchanged build-time TX/RX roles", "Both TX and RX images", "no runtime TX ↔ RX role switching") are superseded by the `ble-runtime-0004` single-image runtime-role architecture. See [ble-runtime-0004](ble-runtime-0004-transceiver-runtime-roles-single-image.md).

## Decision

The shared Transceiver application supports two BLE PHY modes from one codebase with unchanged build-time TX/RX roles:

- **LE Coded PHY S=8 (default).** Preserves the established DL-004 behavior exactly: TX extended advertising with `BT_LE_ADV_OPT_CODED | BT_LE_ADV_OPT_REQUIRE_S8_CODING` plus `CONFIG_BT_EXT_ADV_CODING_SELECTION`; RX coded-only passive scanning. The S=8 coding is requested explicitly through the SDK advertising-coding-selection API; there is no silent S=2 fallback.
- **LE 1M.** TX extended advertising without coded options (default 1M PHY); RX passive scanning with no coded/scan-only options (1M only).

PHY mode is selected at runtime with the board's Button 1 (`sw0` devicetree alias, 200 ms debounce) on both roles. TX preserves its latched `OBS`/`CLR` state across the switch and re-advertises it on the new PHY. RX restarts its scan and resets its deduplication epoch to unknown so stale state from the previous PHY can never be re-emitted.

Role indication is unchanged (TX blinks `led0`+`led1`, RX blinks `led0`). PHY mode is indicated separately on `led2` (on = Coded S=8, off = 1M) so role semantics are never disturbed. Boards must therefore provide the `sw0` and `led2` aliases in addition to the DL-004 LED requirements.

There is deliberately no runtime TX ↔ RX role switching; that behavior was never established and is not introduced here.

## Rationale

Coded S=8 remains the default because range is the priority for the corridor safety signal. LE 1M gives a short-range bench bring-up mode and a second operating point for link comparison without rebuilding or reflashing. A physical button keeps the switch available with no host tooling, and keeping it out of the `OBS`/`CLR` serial protocol avoids any ambiguity on the safety path.

## Consequences

- Both TX and RX images grow a button ISR, a PHY-mode variable, and a transport-restart path; protocol bytes on air and wire are unchanged.
- A PHY switch is a transport restart, not a state transition: RX hosts observe at most one `OBS` for an obstacle that is still present after a switch, and never a `CLR` caused by radio silence (DL-004 consequence preserved).
- TX console may carry rare `ERR adv-restart` / RX console `ERR scan-restart <err>` diagnostics only when a transport restart fails; hosts must ignore non-`OBS`/`CLR` lines.
- Two-board validation (packet exchange, duplicate suppression over air, switching on both ends, S=8 over the real link, LEDs on hardware) is still required.
