# Range–Doppler maps with MTI clutter suppression

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

Turn one raw complex frame into range and Doppler spectra per antenna,
suppress slow-varying clutter by comparing each frame against an
exponential clutter memory (moving-target indication), and integrate
across antennas — producing the Doppler side of the classifier input.

## Position in the pipeline

Upstream: raw `(rx, chirps, samples)` frame from acquisition.
Downstream: per-antenna spectra feed Capon (`profiles[[1, 2]]`) and the
antenna-summed Doppler map feeds the model. On the real-time critical
path every frame.

## Implementation traceability

```text
Implemented by:
- realtime_classifier.py
  - RealtimeRadarClassifier._make_maps()

Called by:
- RealtimeRadarClassifier.process_frame()

Consumes:
- frame_data (SDK frame), self.range_window, self.doppler_window,
  self.dopp_avg (persistent)

Produces:
- elevation_map input (via _capon_map), doppler_map
```

## Signal model

Per antenna, with fast-time samples $x[n]$, $n = 0..N-1$ ($N$ =
`num_samples`), and slow-time chirps $m = 0..M-1$ ($M$ = `num_chirps`):

1. DC removal per chirp: $x_m[n] \leftarrow x_m[n] - \bar{x}_m$.
2. Range FFT on $2N$-padded windowed data, single-sided, scaled by $1/N$:

\[
X_m[k] = \frac{1}{N}\sum_{n=0}^{2N-1} w_R[n]\,x_m[n]\,e^{-j2\pi kn/(2N)},
\qquad k = 0..\tfrac{N}{2}-1
\]

with the $k>0$ bins doubled ($w_R$ = Blackman–Harris).
3. Doppler FFT on $2M$-padded windowed slow-time vectors, scaled by $1/M$:

\[
Y_k[l] = \frac{1}{M}\sum_{m=0}^{2M-1} w_D[m]\,X_m[k]\,e^{-j2\pi lm/(2M)},
\qquad l = 0..2M-1
\]

then `fftshift` on $l$ (zero Doppler centered).
4. Clutter memory update and MTI subtraction per antenna:

\[
\bar{Y} \leftarrow 0.6\,Y + 0.4\,\bar{Y}, \qquad
Y_{\text{MTI}} = Y - \bar{Y}
\]

5. Non-coherent antenna integration: $D = \sum_{\text{ant}} Y_{\text{MTI}}$.

$w_R, w_D$ are the 4-term Blackman–Harris window implemented in
`blackman_harris()` (standard coefficients
0.35875/0.48829/0.14128/0.01168). Padding interpolates; it does not add
true resolution. $\bar{Y}$ persists in `dopp_avg`.

## Inputs

| Item | Form | Meaning |
|---|---|---|
| `frame_data` | `(rx, chirps, samples)` complex | One SDK frame; only antennas 0–2 used |
| `range_window` | `(1, num_samples)` float | Fast-time taper |
| `doppler_window` | `(1, num_chirps)` float | Slow-time taper |
| `dopp_avg` | `(N/2, 2M, 3)` complex | Previous clutter estimate |

## Outputs

| Item | Form | Meaning | Consumer |
|---|---|---|---|
| `doppler_map` | `(N/2, 2M)` complex | Antenna-summed moving-content spectrum | `_prepare_map` → model |
| `range_dopp_prof` | `(3, N/2, 2M)` complex | Per-antenna MTI spectra | Capon pair `[1, 2]` |

## Processing sequence

```text
per antenna: DC removal → BH window → pad ×2 → FFT/N → single-sided ×2
  ↓ transpose
BH window → pad ×2 → FFT/M → clutter update → MTI subtract → fftshift
  ↓
sum over antennas (Doppler map) + stack per-antenna profiles
```

## Parameters

| Parameter | Symbol | Code variable | Units | Value | Meaning | Effect of changing |
|---|---|---|---|---|---|---|
| Range window | $w_R$ | `range_window` | — | BH($N$) | Sidelobe taper | Other windows trade leakage for mainlobe width |
| Doppler window | $w_D$ | `doppler_window` | — | BH($M$) | Same across chirps | Same trade-off |
| Padding | — | `zp1`, `zp2` | — | ×2, ×2 | Spectral interpolation | Larger = smoother peaks, more FFT cost |
| Clutter weights | $\alpha$ | `0.6` / `0.4` literals | — | 0.6 new | Adaptation speed vs smoothness | Higher new-weight follows scene changes faster |
| Antenna count | — | `self.num_rx = 3` | — | 3 (hardcoded) | Antennas integrated | Fixed; extras ignored, fewer raise at construction |

## Assumptions

- Chirps within a frame are uniformly spaced in slow time (SDK sequence).
- Clutter is slow-varying relative to the 0.6/frame adaptation.
- First frame starts from zero clutter memory (initial MTI ≈ 0.6× spectrum).
- Three RX antennas available; pair `[1, 2]` is the intended elevation
  baseline (board orientation TBD).

## Numerical behavior

- Magnitudes are windowed amplitude spectra; no window-gain compensation
  and no power calibration — values are relative.
- Division by `num_samples`/`num_chirps` normalizes FFT length, not window
  energy.
- `dopp_avg` accumulates in complex64; long runs can drift in
  single precision (unmeasured).
- Zero input yields zero maps (no division by data-dependent quantities
  on this path).
- Index bounds assume SDK frame shape matches constructor arguments;
  mismatch raises NumPy errors, not silent corruption.

## Computational characteristics

Per frame: 3 antennas × (range FFT $O(N\log N)$ + Doppler FFT
$O(M\log M)$) plus $O(\text{bins})$ averaging/subtraction; allocations
are per-frame temporaries (`zp1`, `fft1d`, `zp2`) — repeated allocation
on the critical path (documented, not optimized).

## Real-time implications

Executed every frame on the single acquisition thread; the FFT pair per
antenna dominates per-frame DSP cost (unmeasured against the 77 ms
period).

## Failure modes and limitations

| Failure mode | Cause | Symptom | Downstream | Mitigation |
|---|---|---|---|---|
| Stale clutter after scene/sensor move | `dopp_avg` never reset | Suppressed real motion or ghost residue | Biased maps, wrong votes | None (new run only) |
| Shape mismatch vs constructor | SDK config changed at runtime | Exception, recording aborts with partial save | No further frames | Fail-fast |
| Strong near-DC leakage | HP filter/window limits | Residual zero-Doppler ridge | Extra clutter load on MTI | MTI averaging |

## Validation status

Manually inspected only; exercised implicitly in live sessions and in
the hardware-free suite via fakes (no numeric assertions on map
values). No ground-truth range/Doppler accuracy measured.

## References / provenance

No paper/vendor citation in code. "ElephasCare maps" named in the class
docstring — provenance of that term is not recorded in the repository.
