# DSP serial integration boundary

## Contents

- [Why this directory exists](#why-this-directory-exists)
- [Components](#components)
- [System boundary](#system-boundary)
- [Tests](#tests)
- [Links](#links)

## Why this directory exists

The rolling vote in `../collect_data_realtime.py` produces display
labels; the NRF Transceiver TX consumes `OBS`/`CLR` lines. This package
owns everything between those two contracts and nothing else: the
semantic obstacle latch and the serial transport. DSP mathematics never
sees COM ports; the serial writer never sees spectra, tensors, or votes.

## Components

- [`obstacle_state.py`](obstacle_state.py) — `ObstacleStateAdapter`:
  `CLEAR`/`OBSTACLE` latch over voted labels (`Person detected` /
  `Robot detected` → obstacle, `Nothing detected` → clear, anything
  else holds state and records a fault). Initializes `CLEAR` (matches
  NRF boot) with no startup emission; returns the new state only on
  transitions.
- [`serial_output.py`](serial_output.py) — `SerialStateOutput`: renders
  `OBSTACLE → b"OBS\n"`, `CLEAR → b"CLR\n"` at 115200 baud, writes only
  when the transport lags the semantic state (`last_transmitted`
  tracking doubles as retry after failed writes), surfaces transport
  errors instead of hiding them, closes cleanly without emitting on
  shutdown.

## System boundary

Upstream: voted-label strings from
`../collect_data_realtime.py:record_frames()`. Downstream: NRF TX
console bytes. Enabled only via an explicit `--serial-port` (refused
under placeholder inference without the explicit
`--serial-allow-placeholder` development override).

## Tests

`../tests/test_serial_integration.py`: FSM table (init, enter, persist,
clear, unknown-hold, episode `OBS`/`CLR`), exact framing bytes,
no-write cases, failure surfacing, retry semantics. Hardware-free
(injected fake stream).

## Links

- [`../docs/serial-integration-point.md`](../docs/serial-integration-point.md) —
  insertion point, transition semantics, NRF contract, blockers.
- [`../docs/state-machines.md`](../docs/state-machines.md) — SM-7
  implemented record and terminology verdicts.
