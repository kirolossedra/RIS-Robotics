# Wireless Transport Subsystem

## Contents

- [Responsibility](#responsibility)
- [Boundary](#boundary)
- [Runtime modes](#runtime-modes)
- [Maturity](#maturity)

## Responsibility

Transport compact obstacle state from the sensing host to the Controlled Robot-side host without carrying raw radar data.

## Boundary

```text
DSP host -> serial -> TX Transceiver -> BLE -> RX Transceiver -> serial -> RX host
```

The transport owns state delivery, not robot motion policy.

## Runtime modes

One shared nRF52833 firmware image supports runtime TX/RX role switching and Coded S=8 / LE 1M PHY switching.

The RX also contains explicit **Stub** receive-source modes used to test downstream behavior independently of natural over-air reception.

## Maturity

The default Coded S=8 `OBS`/`CLR` path and RX deduplication have physical two-board evidence. Some runtime-switch and host-logger validations remain open. Stub validation is tracked separately from natural-path validation.
