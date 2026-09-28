# Decision: Single-Image Transceiver with Runtime Roles

**ID:** `ble-runtime-0004`
**Previous ID:** `DL-008`
**Status:** Accepted — current architecture
**Date:** 2026-09-28
**Scope:** Transceiver firmware image, runtime roles, buttons, LEDs, boot behavior
**Supersedes:** `ble-runtime-0002` (build-time roles; coded-only PHY), `ble-runtime-0003` (build-time-role statements)

## Decision

There is ONE Transceiver firmware image. The same binary operates as either TX or RX, and the board changes role at runtime using a physical button:

- **Button 2** (board alias `sw1`, 200 ms debounce) toggles the operating role: TX ↔ RX, while running, with no reboot and no reflash.
- **Button 1** (board alias `sw0`, 200 ms debounce) toggles the BLE PHY: LE Coded S=8 ↔ LE 1M, in either role (`ble-runtime-0003` PHY content preserved).
- Role and PHY are independent dimensions: switching one preserves the other, so all four combinations (TX/RX × S=8/1M) are reachable.
- Boot default is **TX + Coded S=8**. There is no persistent role storage (no NVS/settings): every boot starts as TX.
- Role indication is continuous: TX blinks `led0`+`led1`, RX blinks `led0`. PHY is shown independently on `led2` (on = Coded S=8, off = 1M). Role and PHY are both readable without a debugger.
- Boards must provide the `led0`, `led1`, `led2`, `sw0`, and `sw1` aliases (verified present with identical pins on both the previously assumed nRF52840 DK and the actual nRF52833 DK: `led0/1/2` on P0.13/14/15 active-low, `sw0` = Button 1, `sw1` = Button 2; board re-identified via FICR 2026-09-28).

## Role-switch execution

TX → RX: stop advertising and delete the advertiser; discard partial UART input; initialize the RX dedup epoch to unknown; start scanning on the current PHY; force `led1` off.

RX → TX: stop scanning; clear RX transient state; re-initialize the TX latch to `CLR`; flush stale UART bytes so pre-switch input can never become a command; advertise `CLR` on the current PHY.

In RX mode incoming serial bytes are never consumed as commands; in TX mode only exact `OBS`/`CLR` lines act. A role becomes active only after its transport starts; transport-start failures emit a rare `ERR scan-start` / `ERR adv-start` console diagnostic, restore the previous side when possible, and otherwise leave the role LEDs dark rather than showing a normal pattern.

## Rationale

Two physical boards no longer need two firmware images, two build configurations, or role-specific flashing: flash the same `.hex` on both, press Button 2 once on the Jackal-side board, and the link roles are assigned. Keeping selection on physical buttons (not in the serial protocol) preserves the `OBS`/`CLR` safety-path discipline, and keeping PHY orthogonal to role preserves the `ble-runtime-0003` link-comparison use without rebuilds.

## Consequences

- `tx.conf` / `rx.conf` and the TX/RX Kconfig role choice are removed; `prj.conf` enables both broadcaster and observer. One pristine build (`build/transceiver`) produces the only image.
- The BLE packet format is unchanged (connectionless ext-adv, passive scan, same UUID, version `0x01`, state byte); a role switch only changes which side of the same protocol the board performs.
- Two-board validation is still required: same-image packet exchange, role switching on hardware, PHY switching in both roles, LEDs on hardware, UART integration in both roles, range/reliability.
