# Rolling vote (prediction smoothing)

## Contents

- [Purpose](#purpose)
- [Position in the pipeline](#position-in-the-pipeline)
- [Implementation traceability](#implementation-traceability)
- [Signal model](#signal-model)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Processing sequence](#processing-sequence)
- [Parameters](#parameters)
- [Assumptions](#assumptions)
- [Numerical behavior](#numerical-behavior)
- [Computational characteristics](#computational-characteristics)
- [Real-time implications](#real-time-implications)
- [Failure modes and limitations](#failure-modes-and-limitations)
- [Validation status](#validation-status)
- [References / provenance](#references--provenance)

## Purpose

Turn a stream of per-window predictions into a stable displayed result:
the majority label wins, and ties go to the label with the higher mean
winning-output score.

## Position in the pipeline

Upstream: `(label, score)` per 10-frame prediction from the adapter.
Downstream: terminal line + GUI status text. Display-only decision —
not a detection threshold and not a serial trigger.

## Implementation traceability

```text
Implemented by:
- collect_data_realtime.py
  - vote_predictions(predictions)
  - prediction_votes = deque(maxlen=VOTE_WINDOW_PREDICTIONS) in record_frames()

Called by:
- record_frames() after every non-None prediction

Consumes:
- recent (class_name, confidence) pairs

Produces:
- (voted_name, voted_score, vote_count)
```

## Signal model

Given votes \(V = \{(l_i, s_i)\}_{i=1}^{m}\), \(m \le 5\):

\[
\text{count}(l) = |\{i : l_i = l\}|, \qquad
\mathcal{T} = \arg\max_l \text{count}(l)
\]

\[
l^* = \arg\max_{l \in \mathcal{T}} \;\; \text{mean}\{s_i : l_i = l\},
\qquad
\text{score}^* = \text{mean}\{s_i : l_i = l^*\}
\]

Voting starts with the first prediction (short window, not padded).
Each displayed result therefore describes recent frames, not one frame.

## Inputs

| Item | Form | Meaning |
|---|---|---|
| `predictions` | sequence of `(str, float)` | Recent labels + winning scores; length ≤ 5, ≥ 1 in practice |

## Outputs

| Item | Form | Meaning | Consumer |
|---|---|---|---|
| `voted_name` | str | Displayed label | GUI + terminal |
| `voted_score` | float | Mean score of the winning label's votes | Terminal `%` display |
| `vote_count` | int | Winner's vote count | Terminal `n/m` display |

## Processing sequence

```text
append (label, score) to deque(≤5)
  ↓ count labels → majority set
  ↓ tie-break by mean winning score
  ↓ print + GUI update
```

## Parameters

| Parameter | Symbol | Code variable | Units | Value | Meaning | Effect of changing |
|---|---|---|---|---|---|---|
| Window | \(m\) | `VOTE_WINDOW_PREDICTIONS` | predictions | 5 | Smoothing horizon (~3.9 s at full window) | Larger = steadier, slower to react |
| Tie-break | — | mean-score `max` | — | — | Deterministic ties | Score-scale dependent by construction |

## Assumptions

- Successive window predictions are comparable (non-overlapping windows
  keep votes independent in time).
- Scores are comparable across labels (true for one softmax-like head;
  TBD for the actual model file).

## Numerical behavior

- Means over ≤5 floats; no overflow concern.
- Empty input would raise in `max()` — unreachable: called only after an
  append. (Relies on call-site discipline, not a guard.)

## Computational characteristics

\(O(m)\), \(m \le 5\). Negligible.

## Real-time implications

None — constant-time display smoothing outside acquisition/DSP cost.

## Failure modes and limitations

| Failure mode | Cause | Symptom | Downstream | Mitigation |
|---|---|---|---|---|
| Flicker on alternating labels | 1-vote margin swings | Display oscillates | Operator distrust | Longer window (untested trade-off) |
| Stale result after scene change | ≤5 old votes linger | Delayed transition (≤ ~3.9 s) | Display lags reality | Shorter window |
| Score-scale mismatch | Non-calibrated outputs | Tie-break favors wrong label | Misleading winner | None (needs calibrated model) |

## Validation status

Count-then-score behavior (majority wins; 1–1 tie goes to higher mean
score) and first-prediction immediacy verified by unit tests —
executed 2026-09-28, PASS. No on-air tuning validation.

## References / provenance

None recorded; straightforward majority filter with score tie-break.
