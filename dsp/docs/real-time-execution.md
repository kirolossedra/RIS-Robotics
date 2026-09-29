# Real-time execution

## Contents

- [Purpose](#purpose)
- [Startup order](#startup-order)
- [Runtime loop](#runtime-loop)
- [Timing model](#timing-model)
- [Persistent state](#persistent-state)
- [Deadline and latency](#deadline-and-latency)
- [Failure behavior](#failure-behavior)

## Purpose

How the DSP code runs as a continuous real-time program: startup,
per-frame loop, cadence, state, and what happens when things go wrong.
No measured timing exists — requirements and expectations are labeled
as such.

## Startup order

1. Settings printed; operator presses Enter (`main()`).
2. `DeviceFmcw()` context opens the radar; SDK version and sensor type
   printed; `num_rx_antennas` read from the sensor.
3. Metrics + chirp overrides programmed; actual `num_chirps` /
   `num_samples` read back and printed.
4. Classifier constructed (model file loaded, windows/steering/clutter
   buffers allocated; raises `ValueError` if `num_rx < 3`).
5. `warm_up()`: one dummy inference on zeros (model init cost paid
   before frames arrive; does not touch frame buffers).
6. GUI and optional live plot created.
7. `record_frames()` loop runs to 512 frames, stop, close, or error.
8. `stop_acquisition()` (always attempted), partial/full `.npy` save,
   summary; GUI keeps the last result until closed.

## Runtime loop

```text
pump GUI, check stop/close
        ↓
blocking get_next_frame (≤1000 ms timeout)
        ↓
store frame ─→ live-plot update (optional)
        ↓
_make_maps → append to segments
        ↓ (every 10th frame)
normalize → predict → clear segments
        ↓
append vote → majority/tie-break → print + GUI update
        ↓
progress update ─→ next frame
```

Single-threaded: acquisition, DSP, inference, voting, and Tk pumping
share one loop iteration. There is no worker thread, queue, or
frame-drop accounting.

## Timing model

| Item | Value / behavior | Status |
|---|---|---|
| Acquisition period | `1 / 12.94 Hz` ≈ 77.3 ms (SDK `repetition_time_s`) | Configured, not measured |
| Frame read | Blocking, 1000 ms SDK timeout | Implemented |
| Prediction cadence | Every 10 frames ≈ 0.77 s | Implemented |
| Display smoothing | Rolling ≤5 predictions | Implemented |
| Warm-up | One zero-input inference pre-acquisition | Implemented |
| GUI pump | `root.update()` every loop iteration | Implemented; Tk on the critical path |
| Inference backend | Keras `predict(verbose=0)`, CPU/GPU per environment | Environment-dependent, unmeasured |
| Frame-drop detection | None — no sequence counters checked | Gap |

Architectural requirement: per-frame work should fit inside the 77 ms
period and inference inside the 0.77 s window, i.e.
\(T_{\text{processing}} < T_{\text{frame interval}}\).
Whether it is satisfied is **not currently measured** — especially the
per-range-bin `pinv` Capon cost and the Keras inference latency on the
deployment machine.

Conceptual latency (no numbers measured):

\[
T_{\text{decision}}
=
T_{\text{acquisition}}
+
T_{\text{DSP}}
+
T_{\text{decision logic}}
+
T_{\text{output}}
\]

plus up to one 10-frame window of observation delay inherent in the
windowing design.

## Persistent state

`dopp_avg` clutter memory (never cleared mid-run — a moved sensor or
changed scene leaves stale clutter until it adapts at 0.6/frame);
10-frame segments (cleared per prediction); vote deque (rolling);
capture buffer/counter; GUI and plot objects. See
[`signal-processing-pipeline.md`](signal-processing-pipeline.md) table.

## Failure behavior

| Condition | Behavior (from code) |
|---|---|
| Stop button / window close | Loop breaks at next iteration; acquired frames saved |
| Ctrl+C | `KeyboardInterrupt` caught; partial save; message |
| `get_next_frame` raises | Propagates after partial save and `stop_acquisition()` attempt |
| Inference raises | Propagates, but the triggering frame was already stored |
| `stop_acquisition` raises | Propagates after the save still runs |
| Zero frames acquired | No file written; message printed |
| Slow frame (SDK timeout 1000 ms) | Exception path above; no catch-up or drop counting |
| Slow inference/GUI | Loop slips; frames arrive late; no overrun handling |
| Missing model file | `load_model` raises at startup, before acquisition |
| Output mapping mismatch | `ValueError` at startup if indices don't cover outputs exactly once |
| Unknown GUI status string | `ValueError` from `update_status` |
| `num_rx < 3` sensor | `ValueError` at classifier construction |
| Downstream serial/ROS unavailable | Not applicable — no such output exists yet (planned boundary: [`serial-integration-point.md`](serial-integration-point.md)) |

Undefined: behavior on late/lost frames beyond the SDK timeout,
recovery without restart, and any timing guarantee.
