# DSP algorithms — index

## Contents

- [Pipeline order](#pipeline-order)

## Pipeline order

| # | Algorithm | Purpose | Stage | Implementation | Document |
|---|---|---|---|---|---|
| 1 | Range–Doppler maps + MTI | Per-antenna range/Doppler spectra with clutter suppression and antenna integration | Per-frame features | `realtime_classifier.py` → `RealtimeRadarClassifier._make_maps()` | [`range-doppler-mti.md`](range-doppler-mti.md) |
| 2 | Capon beamforming | Super-resolution angle spectrum over one antenna pair | Per-frame features | `realtime_classifier.py` → `RealtimeRadarClassifier._capon_map()` | [`capon-beamforming.md`](capon-beamforming.md) |
| 3 | CNN-LSTM adapter | Windowing, normalization, inference, label mapping | Every 10th frame | `realtime_classifier.py` → `process_frame()`, `_prepare_map()`, `_normalize_timesteps()`, `_predict()`, `warm_up()` | [`cnn-lstm-adapter.md`](cnn-lstm-adapter.md) |
| 4 | Rolling vote | Majority smoothing of predictions with score tie-break | Display decision | `collect_data_realtime.py` → `vote_predictions()`, `record_frames()` deque | [`rolling-vote.md`](rolling-vote.md) |

Diagnostic-only processing (`compute_live_bin_mag`: Hanning window,
single FFT, bin-1 magnitude) is documented in
[`../signal-processing-pipeline.md`](../signal-processing-pipeline.md)
and not given a dedicated algorithm document. Commented-out azimuth
code is legacy, not an algorithm.
