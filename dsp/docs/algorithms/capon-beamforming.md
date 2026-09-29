# Capon beamforming (elevation angle spectrum)

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

Estimate signal power versus angle for each range bin from a single
two-antenna snapshot, giving the classifier spatial (elevation)
resolution beyond one broadside beam. Capon's minimum-variance response
adapts nulls to the measured interference, unlike fixed beamforming.

## Position in the pipeline

Upstream: per-antenna MTI spectra from `_make_maps` (antennas `[1, 2]`
only). Downstream: elevation map → `_prepare_map` → model input 1.
Real-time critical path every frame.

## Implementation traceability

```text
Implemented by:
- realtime_classifier.py
  - RealtimeRadarClassifier._capon_map()

Called by:
- RealtimeRadarClassifier._make_maps() (elevation only; the azimuth
  call is present but commented out)

Consumes:
- range_dopp_prof[[1, 2]] (2 antennas × range bins × Doppler bins),
  self.a_phi (steering vector)

Produces:
- elevation_map (range bins × angle points)
```

## Signal model

For each range bin, with the 2-antenna snapshot across Doppler bins
\(X \in \mathbb{C}^{L \times 2}\) (\(L = 2M\)):

1. Sample covariance (code: `hermitian = (1/M)·XᴴX`, i.e. normalized by
   chirp count, not snapshot count):

\[
\hat{R} = \frac{1}{M} X^H X, \qquad R^{-1} = \mathrm{pinv}(\hat{R})
\]

2. Steering matrix over `angle_len = 2M` angles
   \(\theta \in [-\pi/2, \pi/2]\), two columns \([1,\ a(\theta)]\),
   with \(a(\theta) = e^{-j\pi\sin\theta}\).
3. Batched Capon response (code `einsum("ai,rij,aj->ra", …)`):

\[
P[r, a] = \frac{1}{s_a^H\, R_r^{-1}\, s_a},
\qquad s_a = \begin{bmatrix}1 \\ a(\theta_a)\end{bmatrix}
\]

computed for all range bins \(r\) and angles \(a\) at once. Zero
denominators yield 0 (`where=denominator != 0`).

The two-column steering (reference element 1 plus steered element) is
the standard two-sensor Capon form; the `π` phase factor encodes the
half-wavelength element-spacing assumption
(\(\phi = 2\pi (d/\lambda)\sin\theta\) with \(d/\lambda = 1/2\)).

## Inputs

| Item | Form | Meaning |
|---|---|---|
| `profiles` | `(2, range_bins, doppler_bins)` complex | MTI spectra of antennas 1 and 2 |
| `steering_vector` | `(2·chirps,)` complex | `a_phi`: assumed array response vs angle |

## Outputs

| Item | Form | Meaning | Consumer |
|---|---|---|---|
| elevation map | `(range_bins, 2·chirps)` real | Capon power vs angle per range bin | `_prepare_map` |

## Processing sequence

```text
move antenna axis last → per-bin Hermitian covariance / M
  ↓
pseudo-inverse per bin (pinv)
  ↓
batched quadratic form over steering grid (einsum)
  ↓
reciprocal with zero guard
```

## Parameters

| Parameter | Symbol | Code variable | Units | Value | Meaning | Effect of changing |
|---|---|---|---|---|---|---|
| Antenna pair | — | `profiles[[1, 2]]` | indices | fixed | Interferometric baseline | Different pair = different baseline/orientation |
| Angle grid | \(\theta\) | `phi_vec` | rad | `linspace(-π/2, π/2, 2M)` | Look directions | Finer grid = smoother peaks, linear cost |
| Spacing factor | \(d/\lambda\) | `π` in exponent | — | 1/2 implied | Array geometry | Wrong spacing misplaces/scales angle peaks |
| Covariance scale | \(1/M\) | `1 / self.num_chirps` | — | 1/chirps | Absolute power scale | Cancels in relative use; kept for interpretability |

## Assumptions

- Narrowband snapshot model per range-Doppler bin.
- Two-element array with \(d = \lambda/2\) spacing; mutual coupling ignored.
- Pair `[1, 2]` spans the elevation direction (board orientation TBD).
- Snapshots (Doppler bins) are sufficiently stationary within one frame.
- `pinv` default conditioning is adequate (no diagonal loading).

## Numerical behavior

- `pinv` on rank-deficient/singular covariances (few snapshots, coherent
  sources) yields large responses; only the final reciprocal is guarded.
  No diagonal loading or regularization is applied — documented risk.
- Zero-input test passes (all-zero profiles → finite output via the
  `where` guard); equivalence with the explicit-loop form holds to
  `rtol=1e-11, atol=1e-12` (see Validation).
- Complex64 path with float64 intermediates in places (`pinv` upcasts);
  precision behavior unmeasured beyond the equivalence test.

## Computational characteristics

Per frame: one batched `pinv` over `range_bins` 2×2 matrices
(\(O(\text{bins})\), trivially small per matrix) plus the
\(O(\text{bins} \times \text{angles})\) einsum. The angle grid
(\(2M\)) dominates output size. Dominant per-frame cost alongside the
FFTs (unmeasured).

## Real-time implications

Runs every frame on the acquisition thread; no allocation-free
guarantee (temporaries per call). The refactor comment in the repo
README notes the batching was introduced specifically to cut overhead
while keeping the same calculation.

## Failure modes and limitations

| Failure mode | Cause | Symptom | Downstream | Mitigation |
|---|---|---|---|---|
| Coherent/multipath sources | Rank-deficient covariance, no loading | Split/suppressed peaks | Degraded elevation map | None |
| Wrong pair/geometry | Board rotated vs assumption | Angle axis meaningless | Model sees misleading spatial map | None (undocumented geometry) |
| Singular bins | Empty Doppler bins | Large spurious spikes (guarded only at reciprocal) | Noisy map rows | None |

## Validation status

Equivalence vs the original explicit-loop calculation verified by unit
test (seeded random + all-zero inputs, `1e-11` tolerance) — executed
2026-09-28, PASS. No angle-accuracy measurement against known target
positions; antenna geometry unverified.

## References / provenance

No citation in code. "Capon" names the minimum-variance distortionless
response family; no specific paper is recorded — provenance not
established beyond the method name.
