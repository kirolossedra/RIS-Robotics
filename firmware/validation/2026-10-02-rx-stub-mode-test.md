# RX Reception Stub Mode Test — 2026-10-02

## Setup

- Board: nRF52833 DK, probe `1050670813`
- Image: `nrf52833dk/nrf52833`, nRF Connect SDK `v3.2.3`
- Clean build passed: FLASH 117,596 B; RAM 22,052 B.
- Flash programming and verification passed; the board reset and ran.
- Physical LED mapping: LED1=`led0`, LED2=`led1`, LED3=`led2`, LED4=`led3`.

## Board observations

| Input/action | Expected indication | Observed |
| --- | --- | --- |
| Boot in TX | LED2 and LED3 on; LED1 and LED4 off | Pass |
| Button 2 to RX Natural | LED1 and LED3 on; LED2 and LED4 off (no TX board nearby) | Pass |
| Button 3 to Forced CLR | LED4 steady; LED2 pulses | Pass |
| Button 3 to Forced OBS | LED4 blinks; LED2 pulses | Pass |
| Button 3 back to Natural | LED4 off; LED2 idle without a transmitter | Pass |

The RX console capture did not return a complete state line during this check, so serial `CLR`/`OBS` emission is not marked as hardware-verified. Natural packet suppression in forced modes also remains open because no second TX board was connected for this test.
