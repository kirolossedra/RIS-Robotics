# Runtime Transceiver Modes

## Contents

- [Capability](#capability)
- [Maturity](#maturity)
- [Modes](#modes)
- [Open validation](#open-validation)

## Capability

Use one firmware image for both TX/RX roles and switch role/PHY at runtime.

## Maturity

**Implemented; partially hardware-validated.**

## Modes

- role: TX or RX;
- PHY: Coded S=8 or LE 1M;
- role and PHY are independent dimensions.

## Open validation

Dedicated coordinated role/PHY switch behavior, LE 1M link behavior, and longer-run characterization remain open.
