# DSP hardware-free tests

## Contents

- [What is covered](#what-is-covered)
- [How to run](#how-to-run)
- [Environment notes](#environment-notes)

## What is covered

`test_realtime_detection.py` (14 checks, `unittest`, no radar or model
file needed):

- Capture: full 512-frame save with shape/dtype/content checks, early
  stop, closed GUI (no capture, no file), Ctrl+C partial save,
  read/inference/stop errors (partial data preserved, hardware stopped).
- Predictions: vote count-then-score behavior, all 7 legacy outputs
  mapped to supported labels, 10-frame windowing cadence, warm-up
  isolation from real buffers.
- Capon: batched `_capon_map` equivalence vs the explicit-loop form
  (seeded random + all-zero inputs, `rtol=1e-11`).
- GUI: completion keeps the last detection; unknown statuses raise.

Fakes (`FakeRadar`, `FakeGUI`, `FakeClassifier`, injected `predict`)
stand in for hardware, display, and the model. The Capon check runs the
real implementation against an inline reference.

## How to run

From `dsp/` with the project Python environment:

```powershell
.\.venv_tf\Scripts\python.exe -m unittest discover -s tests -v
```

## Environment notes

The suite imports the real modules, so `ifxradarsdk`, `matplotlib`, and
`tkinter` must be importable even though no hardware is touched —
`requirements.txt` does not cover the SDK, so a bare environment fails
at import. On 2026-09-28 the suite was executed with a minimal local
SDK stub (outside the repo) and passed 14/14 in 0.715 s; see
[`../docs/validation-and-performance.md`](../docs/validation-and-performance.md).
`keras` is only imported inside the classifier constructor, which the
tests bypass — no model file needed.
