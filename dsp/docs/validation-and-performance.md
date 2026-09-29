# Validation and performance

## Contents

- [Purpose](#purpose)
- [Evidence inventory](#evidence-inventory)
- [Unit-test execution 2026-09-28](#unit-test-execution-2026-09-28)
- [Explicitly not measured](#explicitly-not-measured)
- [Gaps](#gaps)

## Purpose

Evidence only: what has actually been run, observed, or measured for
DSP — and what has not. Implementation existence is never treated as
validation here.

## Evidence inventory

| Item | Description |
|---|---|
| Component | Obstacle-state FSM + serial output (`dsp/integration/`) |
| Method | 14 hardware-free unit tests (FSM table, episode, framing, no-write cases, failure/retry, record_frames wiring with fake stream) |
| Input/data | Label sequences incl. unknowns; fake serial stream with fail mode |
| Expected behavior | Transition-only exact `b"OBS\n"`/`b"CLR\n"`; holds on unknown; init silence; retry after failure |
| Observed behavior | 14/14 PASS (with the 14 pre-existing DSP tests: 28/28 total, 2026-09-28) |
| Pass criterion | `unittest` OK |
| Current status | PASS in software; hardware validation pending |
| Evidence | `dsp/tests/test_serial_integration.py` |

| Item | Description |
|---|---|
| Component | Hardware-free unit suite `dsp/tests/test_realtime_detection.py` |
| Method | `python -m unittest discover -s tests -v` (14 tests: capture/save paths, voting, windowing, warm-up, Capon equivalence, GUI completion behavior) |
| Input/data | Faked radar/GUI/classifier; synthetic NumPy frames; seeded RNG for Capon check |
| Expected behavior | Per-test asserts (shapes, dtypes, counts, vote outcomes, equivalence to `1e-11`) |
| Observed behavior | 14/14 PASS in 0.715 s on 2026-09-28 |
| Pass criterion | `unittest` OK |
| Current status | PASS (with SDK stub — see below) |
| Evidence | This section; temp stub scripts (not committed) |

| Item | Description |
|---|---|
| Component | Live acquisition + placeholder display |
| Method | Joint Radar/RIS sessions (Husky as moving target, bags-on-top visibility intervention, Doppler/range signature observation) |
| Input/data | Real corridor scenes, robot + human motion |
| Expected behavior | Sensing responds to motion; pipeline runs end to end |
| Observed behavior | Campaign completed 2026-09-17; signatures characterized qualitatively |
| Pass criterion | Not formally defined |
| Current status | Inconclusive as detector validation (placeholder model) |
| Evidence | `session-logs/2026-09-17.md`, `decision-logs/robot-runtime-0002-*.md` |

| Item | Description |
|---|---|
| Component | Capon batching refactor |
| Method | Equivalence test vs explicit per-element loop (incl. all-zero input) |
| Observed behavior | Match to `rtol=1e-11, atol=1e-12` |
| Current status | PASS (in suite above) |
| Evidence | `test_batched_capon_matches_original_calculation` |

## Unit-test execution 2026-09-28

Environment on this machine: `numpy` 2.5.2, `matplotlib` and `tkinter`
present; `ifxradarsdk` and `keras` absent; model file absent
(`*.keras` is git-ignored). The suite imports the real modules, so it
cannot run unmodified here. It was executed with a minimal local
`ifxradarsdk` stub (outside the repo; `get_version_full`,
`DeviceFmcw`, `FmcwMetrics`, `FmcwSimpleSequenceConfig` only — the
tests never touch real hardware paths, and no test calls model loading
except through injected fakes):

```text
Ran 14 tests in 0.715s — OK (14/14 PASS)
```

This validates capture logic, voting, windowing, warm-up isolation, the
Capon refactor, placeholder mapping, and GUI completion behavior — not
radar data, model quality, timing, or the SDK.

## Explicitly not measured

- Frame processing latency, inference latency, GUI overhead, CPU/RAM use.
- Whether per-frame work fits the 77 ms acquisition period.
- Range/velocity accuracy against ground truth.
- Detection precision/recall, false-alarm rate (no trained detector).
- Capon angle accuracy or antenna-geometry verification.
- Repeatability across runs, positions, subjects.
- Behavior on dropped/late frames (no drop accounting exists).

## Gaps

- `requirements.txt` lists only `keras`/`tensorflow`: no numpy,
  matplotlib, SDK, or version pins — no reproducible environment.
- Tests require `ifxradarsdk` importable even though fully faked;
  untested on machines without it (as found here).
- Default save path is a personal Windows path, overwritten per run.
- The `.keras` model file is absent from the repo (git-ignored).
- No calibration procedure, no ground-truth dataset, no benchmark
  outputs exist in the repository.
