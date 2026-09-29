# Parameters and tuning

## Contents

- [Purpose](#purpose)
- [Hardware-derived parameters](#hardware-derived-parameters)
- [Signal-derived parameters](#signal-derived-parameters)
- [Algorithm configuration](#algorithm-configuration)
- [Experimentally tuned parameters](#experimentally-tuned-parameters)
- [Runtime/control parameters](#runtimecontrol-parameters)
- [Key relationships](#key-relationships)

## Purpose

Subsystem parameter registry: where each value lives, what it means,
and what changing it does — only where the code or mathematics supports
the claim. Untuned rationale is stated, not invented.

## Hardware-derived parameters

Set in `collect_data_realtime.main()`; dictated by (or for) the radar hardware.

| Parameter | Location | Units | Current value | Role / consequence |
|---|---|---|---|---|
| `chirp.start_frequency_Hz` | `main()` | Hz | 59_250_000_000 | Sweep start; with end sets 3 GHz bandwidth → 0.05 m range resolution |
| `chirp.end_frequency_Hz` | `main()` | Hz | 62_250_000_000 | Sweep end |
| `chirp.sample_rate_Hz` | `main()` | Hz | 2_000_000 | ADC rate; with chirp duration sets sample count (SDK-computed) |
| `chirp.rx_mask` | `main()` | bitmask | all RX | Enables every sensor antenna (classifier needs ≥3) |
| `chirp.tx_mask` | `main()` | bitmask | 1 | Single transmitter (no MIMO) |
| `chirp.tx_power_level` | `main()` | SDK steps | 31 | Transmit power (maximum step assumed; not documented in repo) |
| `chirp.if_gain_dB` | `main()` | dB | 23 | IF amplifier gain; higher = more sensitivity and earlier saturation |
| `chirp.lp_cutoff_Hz` | `main()` | Hz | 500_000 | Anti-alias / IF low-pass edge |
| `chirp.hp_cutoff_Hz` | `main()` | Hz | 80_000 | DC/leakage high-pass edge |
| Center 60.75 GHz (metrics) | `FmcwMetrics` | Hz | 60_750_000_000 | Consistent with (start+end)/2; sets λ ≈ 4.94 mm for Doppler scaling |

## Signal-derived parameters

Computed by the SDK from the requested metrics; read back and printed.

| Parameter | Location | Units | Current value | Role / consequence |
|---|---|---|---|---|
| `num_chirps` | Sequence readout | count | TBD at runtime | Doppler FFT length basis (×2 after padding); Capon covariance divisor; steering length |
| `num_samples` | Sequence readout | count | TBD at runtime | Range FFT length basis (×2 after padding); window lengths |
| `repetition_time_s` | `sequence.loop` | s | 1/12.94 | Frame cadence |
| Requested `range_resolution_m` 0.05, `max_range_m` 1.6, `max_speed_m_s` 2.0, `speed_resolution_m_s` 0.065 | `FmcwMetrics` | mixed | as listed | Design targets for the SDK chirp synthesis, not measured performance |

## Algorithm configuration

In `realtime_classifier.py` and `collect_data_realtime.py`.

| Parameter | Location | Units | Current value | Role / consequence |
|---|---|---|---|---|
| Range/Doppler windows | `blackman_harris()` | — | 4-term, a0=0.35875… | Sidelobe suppression before each FFT; narrower mainlobe alternatives would trade leakage for resolution |
| Zero-padding factors | `_make_maps` (`zp1`, `zp2`) | — | ×2 both axes | Interpolates spectra (display/peak location), does not add true resolution |
| Clutter weights | `_make_maps` | — | 0.6 new / 0.4 history | Larger new-weight adapts faster to scene changes, smaller smooths noise; memory never reset mid-run |
| Steering `exp(-jπ·sinθ)`, `θ ∈ [-π/2, π/2]` over `2·chirps` points | `__init__` | rad | as listed | Assumes half-wavelength element spacing; wrong spacing misplaces angle peaks |
| Antenna pair `[1, 2]` (elevation) | `_make_maps` | indices | fixed | Selects the interferometric baseline; geometry vs board orientation TBD |
| `target_shape` | classifier init | pixels | (32, 256) | Model input geometry; nearest-neighbor resize, no anti-aliasing |
| Per-timestep epsilon | `_normalize_timesteps` | — | `1e-8` | Guards zero-variance frames; smaller values risk `inf` on flat inputs |
| `CLASSIFICATION_WINDOW_FRAMES` | settings | frames | 10 | Observation delay ≈ 0.77 s; must match the model's expected window |
| `VOTE_WINDOW_PREDICTIONS` | `record_frames` | predictions | 5 | Larger = steadier display, slower to react; starts immediately, not after 5 |
| Tie-break | `vote_predictions` | — | mean winning score | Deterministic; favors confidently-scored labels |

## Experimentally tuned parameters

Thresholds/constants with no documented derivation in the repository:

- `BIN_IDX = 1` (live-plot FFT bin) — implemented, rationale not documented.
- `VOTE_WINDOW_PREDICTIONS = 5`, clutter `0.6/0.4`, TX power 31, IF gain
  23 dB — implemented, tuning rationale not documented.
- `DETECTION_CLASS_NAMES` target order (`0 = person`, `1 = robot`,
  `2 = nothing`) — interface contract for the future trained model.
- Placeholder index→label mapping — explicitly temporary.

## Runtime/control parameters

| Parameter | Location | Current value | Role |
|---|---|---|---|
| `NUM_FRAMES` | settings | 512 | Recording length (≈39.6 s) |
| `FRAME_RATE` | settings | 12.94 | Acquisition cadence (Hz) |
| `FILE_NAME`, `SAVE_FOLDER` | settings | personal Windows path | Capture destination; overwritten each run — change per capture |
| `ENABLE_REALTIME_CLASSIFICATION` | settings | True | Inference on/off |
| `SHOW_DETECTION_STATUS_GUI`, `SHOW_LIVE_PLOT`, `LOCATION_LABEL` | settings | True/False/"RIS Corner" | Display options |
| `CLASSIFICATION_MODEL_PATH`, `PLACEHOLDER_MODE` | settings | `.keras` path / True | Model selection |
| `timeout_ms=1000` | `record_frames` | 1000 ms | Per-frame SDK blocking limit |

## Key relationships

- Bandwidth → range resolution (`c/2B`); changing the sweep changes bin
  scale and the SDK-derived sample count.
- Chirp count → Doppler length, steering length, and `pinv` cost
  (per-range-bin matrix inverse scales with the square of the antenna-pair
  dimension — here trivially 2×2 — while FFT cost scales with chirp count).
- Window length → observation delay (10 frames ≈ 0.77 s) and model
  compatibility (fixed at construction).
- Vote length → display steadiness vs reaction speed.
- TX power / IF gain → sensitivity vs saturation/clutter strength; they
  also shift the operating point the (future) trained model sees.
