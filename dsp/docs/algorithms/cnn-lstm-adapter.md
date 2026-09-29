# CNN-LSTM inference adapter

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

Adapt the radar feature maps to the fixed input contract of a
Keras CNN-LSTM, run inference every 10 frames, and translate raw output
indices into detection labels — currently against an explicit
placeholder activity model, pending a trained detector.

## Position in the pipeline

Upstream: non-overlapping 10-frame `(10, 32, 256)` stacks from
`process_frame()`. Downstream: `(label, score, probabilities)` into the
rolling vote. Real-time path every 10th frame (plus one warm-up
inference pre-acquisition).

## Implementation traceability

```text
Implemented by:
- realtime_classifier.py
  - RealtimeRadarClassifier.process_frame()
  - RealtimeRadarClassifier._prepare_map()
  - RealtimeRadarClassifier._normalize_timesteps() (static)
  - RealtimeRadarClassifier._predict()
  - RealtimeRadarClassifier.warm_up()
  - module constants CLASS_NAMES, DETECTION_CLASS_NAMES,
    PLACEHOLDER_CLASS_NAMES

Called by:
- collect_data_realtime.record_frames() (process_frame)
- warm_up calls _predict directly

Consumes:
- elevation_segment, doppler_segment (lists of (32, 256) maps)

Produces:
- (class_name, confidence, probabilities); None on non-window frames
```

## Signal model

Per 10-frame stack \(X \in \mathbb{R}^{10 \times 32 \times 256}\),
per-timestep (per-frame) standardization:

\[
\hat{X}_{t} = \frac{X_{t} - \mu_{t}}{\sigma_{t}},\quad
\mu_t, \sigma_t \text{ over axes }(1,2),\quad
\sigma_t \leftarrow \max(\sigma_t, \epsilon),\; \epsilon = 10^{-8}
\]

then reshape to \((1, 10, 32, 256, 1)\) per input and model forward
pass \(p = \mathrm{softmax\text{-}like outputs}\), label
\(\hat{c} = \arg\max p\), confidence \(p_{\hat{c}}\). (Whether the model
ends in softmax is a property of the loaded file, TBD — the code only
assumes a probability-like vector.)

## Inputs

| Item | Form | Meaning |
|---|---|---|
| Elevation/doppler stacks | `(10, 32, 256)` float32 each | 10 consecutive resized magnitude maps |
| Model file | `Bathroom_CNNLSTM.keras` (absent from repo) | 7-output activity classifier |
| `class_names` | index→label mapping | Output interpretation contract |

## Outputs

| Item | Form | Meaning | Consumer |
|---|---|---|---|
| `class_name` | str | Mapped label, or `"Unknown class: i"` fallback | Vote deque |
| `confidence` | float | Winning output value | Vote tie-break, terminal |
| `probabilities` | `(n,)` float | Raw output vector | Terminal score context |

## Processing sequence

```text
stack 10 frames (non-overlapping; clear after predict)
  ↓ per-frame z-norm (eps 1e-8)
  ↓ add channel + batch dims
  ↓ model.predict(verbose=0) → argmax → label mapping
  ↓ warm_up once on zeros (pre-acquisition init)
```

## Parameters

| Parameter | Symbol | Code variable | Units | Value | Meaning | Effect of changing |
|---|---|---|---|---|---|---|
| Window | — | `window_frames` | frames | 10 | Model time context (~0.77 s) | Must match the model's expected window |
| Map geometry | — | `target_shape` | pixels | (32, 256) | Model spatial contract | Model-specific; resize is nearest-neighbor, no smoothing |
| Epsilon | \(\epsilon\) | `1e-8` literal | — | 1e-8 | Zero-variance guard | Too small risks `inf` on flat frames |
| Class mapping | — | `PLACEHOLDER_CLASS_NAMES` | — | 0→Person, 1→Robot, 2–6→Nothing | Temporary UI wiring | Replace together with the trained model |
| Target order | — | `DETECTION_CLASS_NAMES` | — | 0=person, 1=robot, 2=nothing | Future detector contract | Must match the trained file's output order |

Legacy note: `CLASS_NAMES` (bathroom activities, indices 0–4 and 6 —
index 5 has no entry) is the original training vocabulary; the
placeholder map covers all 7 model outputs.

## Assumptions

- Model expects exactly two `(1, 10, 32, 256, 1)` float32 inputs in
  [elevation, doppler] order.
- 10-frame non-overlapping windows match training framing (unstated in
  repo — assumed by construction).
- Per-frame normalization matches training preprocessing (unstated —
  assumed).
- Class-index coverage is enforced at load (indices must label every
  output exactly once).

## Numerical behavior

- `abs` → float32 discards phase (magnitude-only model input, by design).
- Nearest-neighbor resize aliases fine structure; no anti-aliasing.
- Zero frames normalize to zeros (epsilon path), safe for warm-up.
- `argmax` ties resolve to the lowest index (NumPy behavior, undocumented
  reliance).

## Computational characteristics

One Keras forward pass per 10 frames on CPU/GPU per environment;
`_normalize_timesteps` is \(O(\text{window} \times \text{pixels})\);
temporary batch/channel arrays allocated per prediction.

## Real-time implications

Largest single latency step; warm-up moves one-time init cost ahead of
acquisition. Runs on the acquisition thread — a slow predict delays the
next frame read (no buffering/queue).

## Failure modes and limitations

| Failure mode | Cause | Symptom | Downstream | Mitigation |
|---|---|---|---|---|
| Missing model file | Absent `.keras` | Exception at startup | No acquisition | Fail-fast before recording |
| Mapping mismatch | Wrong `class_names` | `ValueError` at startup | No acquisition | Coverage check |
| Wrong input geometry | Different trained model | Exception inside predict | Recording aborts, partial save | Fail-fast |
| Placeholder taken literally | UI testing output | False "detections" | Operator confusion | Explicit GUI/terminal banners |
| `azimuth` re-enabled naively | Commented code | 3-input vs 2-input mismatch | Exception | Keep commented until adapter updated |

## Validation status

Mapping coverage (all 7 outputs → supported labels), windowing cadence
(2 predictions in 21 frames), and warm-up isolation verified by unit
tests — executed 2026-09-28, PASS. No detection-accuracy measurement
exists (placeholder model by design).

## References / provenance

`Bathroom_CNNLSTM.keras` filename suggests bathroom activity-monitoring
provenance ("ElephasCare" in the class docstring); no paper, dataset, or
training record in the repository. Provenance otherwise not established.
