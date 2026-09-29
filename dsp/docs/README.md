# DSP engineering documentation — index

## Contents

- [What each document answers](#what-each-document-answers)
- [Suggested reading paths](#suggested-reading-paths)

## What each document answers

```text
signal-processing-pipeline.md
    → How does radar data move through the processing chain?

data-and-signal-contracts.md
    → What are the representations, shapes, units, and interfaces?

real-time-execution.md
    → How does the pipeline behave as a real-time program?

parameters-and-tuning.md
    → Which parameters define the operating point and how are they tuned?

validation-and-performance.md
    → What has actually been measured or validated?

algorithms/
    → What does each substantive DSP algorithm do?
```

| Document | Question it answers |
|---|---|
| [`signal-processing-pipeline.md`](signal-processing-pipeline.md) | Stage by stage: configuration → acquisition → maps → windows → inference → vote → display/save, with files, symbols, and state. |
| [`data-and-signal-contracts.md`](data-and-signal-contracts.md) | Every important signal: code form, shape, dtype, units, timing, consumer. |
| [`real-time-execution.md`](real-time-execution.md) | Startup order, the per-frame loop, cadence, persistent state, failure behavior. |
| [`parameters-and-tuning.md`](parameters-and-tuning.md) | Hardware-derived, signal-derived, algorithm, tuned, and runtime parameters with locations and consequences. |
| [`validation-and-performance.md`](validation-and-performance.md) | Evidence only: unit tests, live sessions, and everything not yet measured. |
| [`algorithms/README.md`](algorithms/README.md) | Algorithm inventory in pipeline order with implementation links. |
| [`state-machines.md`](state-machines.md) | Every control-relevant state machine (vote filter, buffers, clutter memory, GUI latch, NRF latch, proposed adapter) and the raw-vs-stable-vs-control distinction. |
| [`serial-integration-point.md`](serial-integration-point.md) | Exact insertion point, obstacle-state FSM design, transition semantics, NRF contract, blockers. Serial code is not yet written. |

## Suggested reading paths

- New to the subsystem: [`../README.md`](../README.md) → `signal-processing-pipeline.md` → `algorithms/`.
- Changing a threshold or rate: `parameters-and-tuning.md` → the relevant algorithm document.
- Checking a claim: `validation-and-performance.md` first; implementation second.
