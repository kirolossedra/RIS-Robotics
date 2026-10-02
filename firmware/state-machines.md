# Transceiver Firmware State Machines

This note describes the runtime controls and the receive processing behavior in the single Transceiver image. Button numbers refer to the physical buttons on the nRF52833 DK.

## Runtime role and PHY

The firmware boots in TX on LE Coded S=8. Button 2 changes the active role between TX and RX; Button 1 changes the PHY between LE Coded S=8 and LE 1M. A role or PHY change restarts the corresponding BLE transport. The role changes only when the requested transport starts successfully.

Entering RX always selects Natural receive mode. Leaving RX clears the test source mode. Switching PHY while in RX preserves the selected receive source mode and starts a fresh RX deduplication epoch.

## TX state

TX starts in `CLR`. Serial commands and Button 3 both update the same state used by the advertiser:

| Current state | Input | Next state | Physical LED1 |
| --- | --- | --- | --- |
| `CLR` | Serial `OBS` or Button 3 | `OBS` | Blinks while OBS is advertised |
| `OBS` | Serial `CLR` or Button 3 | `CLR` | Off |
| Either | Repeated serial state command | Unchanged | Follows current state |

Physical LED2 indicates the TX role. Physical LED3 indicates the PHY.

## RX receive source

Button 3 cycles the RX receive source. A forced mode overrides real Transceiver packets until the source returns to Natural.

| Current mode | Button 3 | Receive behavior | Physical LED4 | Physical LED2 |
| --- | --- | --- | --- | --- |
| Natural | Select Forced CLR | Process valid over-the-air packets | Off | Pulses for each accepted packet |
| Forced CLR | Select Forced OBS | Ignore real packets; synthesize `CLR` at the configured interval (500 ms default) | Steady on | Pulses for each synthetic event |
| Forced OBS | Return to Natural | Ignore real packets; synthesize `OBS` at the configured interval (500 ms default) | Blinks at 1 Hz | Pulses for each synthetic event |

After Forced OBS, the next Button 3 press returns to Natural. Changing the receive source does not reset duplicate-suppression state. Synthetic and natural states use the same RX state-processing path, so a forced `OBS` followed by forced `CLR` is handled as an ordinary state transition. As in Natural mode, an initial `CLR` in a fresh observation epoch is silent; RX emits `CLR` when it follows an emitted `OBS`.

Physical LED1 indicates the RX role. Physical LED3 indicates the PHY. Physical LED4 is off outside RX.

## Board-check scope

The 2026-10-02 board check confirmed the TX boot LEDs, RX Natural LEDs, Forced CLR LED4/LED2 pattern, Forced OBS LED4/LED2 pattern, and return to Natural. See [the RX stub validation record](validation/2026-10-02-rx-stub-mode-test.md). RX serial output and suppression of real over-the-air packets while forced remain unverified on the board.
