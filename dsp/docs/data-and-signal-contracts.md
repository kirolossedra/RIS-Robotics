# Data and signal contracts

## Contents

- [Purpose](#purpose)
- [Signal inventory](#signal-inventory)
- [Derived radar quantities](#derived-radar-quantities)
- [Conventions and gaps](#conventions-and-gaps)

## Purpose

Exact representations, shapes, types, units, and interfaces of the
signals in `dsp/`, tied to code variables. Physics is stated only where
the implementation or its configuration supports it.

## Signal inventory

| Name | Source | Code representation | Shape | Dtype | Units / meaning | Consumer |
|---|---|---|---|---|---|---|
| Raw frame | `device.get_next_frame()[0]` | `frame_data` (`collect_data_realtime.record_frames`) | `(rx, chirps, samples)`; `rx/chirps/samples` read back from SDK at startup | complex (stored `complex64`) | ADC samples per chirp per antenna; ordering chirps × fast-time | Capture buffer, `_make_maps`, live plot |
| Saved capture | Acquisition loop | `.npy` file (`SAVE_PATH`) | `(frames_acquired, rx, chirps, samples)` | `complex64` | Same as raw frame | Offline analysis (outside repo) |
| Per-chirp mean | `np.average(mat, axis=1)` | temporary in `_make_maps` | `(chirps,)` per antenna | complex | DC estimate per chirp, subtracted (DC removal) | Range windowing |
| Range window | `blackman_harris(num_samples)` | `self.range_window`, `(1, num_samples)` | 1-D taper | float | Sidelobe weighting before range FFT | Range FFT input |
| Range profile | `2 * fft(padded)[:, :N/2] / N` | `range_fft` | `(chirps, num_samples//2)` | complex | Single-sided amplitude spectrum vs fast-time bin | Transpose → Doppler stage |
| Doppler window | `blackman_harris(num_chirps)` | `self.doppler_window`, `(1, num_chirps)` | 1-D taper | float | Sidelobe weighting across chirps | Doppler FFT input |
| Doppler spectrum | `fft(padded) / num_chirps`, `fftshift` axis 1 | `fft2d`, `doppler_fft` | `(num_samples//2, num_chirps*2)` | complex | Slow-time spectrum per range bin; zero-Doppler centered after shift | Clutter average, MTI, antenna sum |
| Clutter memory | Persistent array | `self.dopp_avg` | `(num_samples//2, num_chirps*2, num_rx)` | complex | Exponential average (0.6 new + 0.4 history) of the Doppler spectrum = slow-varying clutter estimate | MTI subtraction |
| MTI output | `fft2d - dopp_avg` | `fft2d_mti` | per antenna, as Doppler spectrum | complex | Current minus clutter = moving-content emphasis | Antenna sum, Capon input |
| Doppler map | Sum over 3 antennas | `doppler_map` | `(num_samples//2, num_chirps*2)` | complex → magnitude later | Non-coherent integration across RX | `_prepare_map` → model input 2 |
| Antenna profiles | Per-antenna MTI spectra | `range_dopp_prof` | `(3, num_samples//2, num_chirps*2)` | complex | Per-antenna range-Doppler before angle processing | Capon (`[[1, 2]]` pair) |
| Steering vectors | `exp(-jπ·sin(angle))` over `linspace(-π/2, π/2, 2·chirps)` | `a_theta`, `a_phi` | `(2·chirps,)` each | complex | Half-wavelength ULA steering assumption (phase `π·sinθ`) | Capon denominator |
| Elevation map | `_capon_map(profiles[[1,2]], a_phi)` | `elevation_map` | `(num_samples//2, 2·chirps)` | real power-like (1/denominator) | Capon spatial spectrum over elevation angle × range | `_prepare_map` → model input 1 |
| Model map | `abs → float32 → resize (32, 256)` | stacked `(10, 32, 256)` | `(window, 32, 256)` | float32, per-frame z-scored | Network input frame | `_predict` |
| Prediction | `argmax(probabilities)` + mapping | `(class_name, confidence, probabilities)` | str, float, `(n_classes,)` | Label + winning softmax score | Vote deque, GUI, terminal |
| Vote result | `vote_predictions(deque≤5)` | `(voted_name, voted_score, vote_count)` | str, float, int | Smoothed display state; the final authoritative classification and the planned serial source (see [`serial-integration-point.md`](serial-integration-point.md)) | GUI + terminal line |
| Live bin magnitude | `mean over RX of |FFT(bin 1)|` | float (from `compute_live_bin_mag`) | scalar per frame | Real-part-only magnitude at FFT bin 1, chirp 0 — diagnostic, see limitations | Live plot |

## Derived radar quantities

From configured values only (`collect_data_realtime.main()`):

| Quantity | Derivation | Value |
|---|---|---|
| RF bandwidth `B` | 62.25 − 59.25 GHz | 3.0 GHz |
| Range resolution | `c / (2B)` | 0.05 m (matches `range_resolution_m`) |
| Center frequency | (59.25 + 62.25)/2 GHz | 60.75 GHz (matches metric) |
| Wavelength `λ` | `c / 60.75 GHz` | ≈ 4.94 mm |
| Frame interval | `1 / 12.94 Hz` | ≈ 77.3 ms |
| Recording length | `512 / 12.94 Hz` | ≈ 39.6 s |
| Prediction cadence | 10 frames at 12.94 Hz | ≈ 0.77 s |
| Max-range bins implied | 1.6 m / 0.05 m | 32 bins |

`num_chirps`, `num_samples`, chirp duration, and sampling window are
computed by the SDK from the metrics and only printed at startup —
TBD for any fixed numbers. `max_speed_m_s` (2.0) and
`speed_resolution_m_s` (0.065) are requested metrics, not measured
resolutions.

## Conventions and gaps

- Range axis: bin index increases with range; exact meters-per-bin needs
  `num_samples` (TBD).
- Doppler axis: `fftshift` centers zero Doppler; approaching-vs-receding
  sign is TBD (depends on chirp direction and SDK sample ordering).
- Angle axis: `linspace(-π/2, π/2)` over field of view; which physical
  antenna pair is elevation vs azimuth (board orientation) is TBD —
  code uses pair `[1, 2]` for elevation.
- Steering assumes half-wavelength element spacing (the `π` factor);
  actual array geometry is TBD.
- Magnitudes are windowed amplitude spectra (no window-gain
  compensation); values are relative, not calibrated power.
- `compute_live_bin_mag` uses `.astype(float)` (real part only), chirp 0
  only, and a Hanning window — inconsistent with the main path's
  Blackman–Harris; diagnostic use only.
