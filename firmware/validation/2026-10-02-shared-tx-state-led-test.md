# Shared TX State and LED Test — 2026-10-02

## Setup

- Board: nRF52833 DK, probe `1050670813`
- Image: `nrf52833dk/nrf52833`, built with nRF Connect SDK `v3.2.3`
- Flash completed with programming verification and reset.
- Physical LED mapping: LED1 = Zephyr `led0`; LED2 = `led1`; LED3 = `led2`.
- TX role indicator: LED2 on. Coded S=8 PHY indicator: LED3 on.

## Checks

| Input/action | Expected physical indication | Observed |
| --- | --- | --- |
| Reset after flash | Default `CLR`; LED1 off, LED2/LED3 on | Pass |
| Send `OBS` on serial (`COM8`, 115200 baud) | LED1 blinks; LED2/LED3 stay on | Pass |
| Send `CLR` on serial | LED1 off; LED2/LED3 stay on | Pass |
| Press Button 3 from `CLR` | Shared state changes to `OBS`; LED1 blinks | Pass |
| Send serial `CLR` after Button 3 sets `OBS` | Serial write clears the same state; LED1 off | Pass |
| Reset | State returns to boot default `CLR`; LED1 off | Pass |

This validates the TX state and indicator paths. RX packet LED behavior, Button 2 role switching, and Button 1 PHY switching were not part of this test.
