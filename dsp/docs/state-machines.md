# DSP state machines

## Contents

- [Purpose](#purpose)
- [Inventory](#inventory)
- [Classification path in detail](#classification-path-in-detail)
- [Three concepts, separated](#three-concepts-separated)
- [Terminology verdicts](#terminology-verdicts)

## Purpose

Every explicit and implicit state machine in the real-time DSP path:
what holds state, how it transitions, what resets it, and what can go
stale. Behavior, not syntax — rolling buffers and persistent numerics
are included where they affect control-relevant behavior, with precise
terminology per component (FSM vs temporal filter vs persistent state).

## Inventory

### SM-1. Recording lifecycle (explicit control FSM)

| Field | Content |
|---|---|
| Purpose | Bound one recording; guarantee the hardware is stopped and data saved on every exit path |
| Implementation | `collect_data_realtime.record_frames()` (`while frame_count < num_frames` + `try/finally`) |
| State representation | `frame_count` counter vs `num_frames` bound; exceptions as transitions |
| Possible states | Collecting, user-stopped (button/close/Ctrl+C), errored, closing-out (stop + save), done |
| Inputs | GUI stop flag/window state, `get_next_frame` outcome, inference outcome, counter |
| Transition conditions | `frame_count == num_frames` → done; stop/close/Ctrl+C → user-stopped; exception → errored; all → closing-out |
| Outputs | Saved `.npy` (acquired frames only), terminal summary, GUI finish state |
| Reset condition | New `record_frames()` call (fresh buffer, counter, vote deque) |
| Persistence | Per recording |
| Failure concern | None structural; silently saves partial data by design (documented behavior, not a fault) |

### SM-2. Prediction windowing (episode accumulator)

| Field | Content |
|---|---|
| Purpose | Assemble non-overlapping 10-frame model inputs |
| Implementation | `RealtimeRadarClassifier.process_frame()`; `elevation_segment`, `doppler_segment` lists |
| State representation | Two buffers, length 0–10 |
| Possible states | Filling (length < 10 → return `None`); complete (length == 10 → predict, clear) |
| Inputs | One map pair per frame |
| Transition conditions | Append per frame; on reaching 10, stack → predict → `clear()` both lists |
| Outputs | `(10, 32, 256)` stacks every 10th frame, else `None` |
| Reset condition | `clear()` after each prediction; fresh lists per classifier instance |
| Persistence | Within a run; never across runs |
| Failure concern | Windows are non-overlapping by construction — a target appearing mid-window waits for the next boundary (≤0.77 s observation granularity) |

### SM-3. Rolling vote (temporal filter with state, not an FSM)

| Field | Content |
|---|---|
| Purpose | Smooth per-window predictions into a displayed result |
| Implementation | `vote_predictions()` over `prediction_votes = deque(maxlen=5)` in `record_frames()` |
| State representation | Up to 5 recent `(label, score)` pairs |
| Possible states | Any multiset of ≤5 labels — a filter state, not a transition graph |
| Inputs | One `(label, score)` per 10-frame prediction |
| Transition conditions | Append (oldest evicted past 5); majority count wins; ties → higher mean winning score |
| Outputs | `(voted_name, voted_score, vote_count)` |
| Reset condition | New recording (new deque); starts voting with the first prediction, never waits for 5 |
| Persistence | Per run |
| Failure concern | No hysteresis: entry and clearing use symmetric majority evidence, so a 3–2 split flickers; ≤5 stale votes delay transitions up to ~3.9 s |

Verdict: rolling-window temporal (majority) filter. It has state but no
latch, no entry/exit thresholds, and no transition conditions beyond the
window contents — calling it hysteresis or an FSM would be incorrect.

### SM-4. Clutter memory (persistent numerical state, not control state)

| Field | Content |
|---|---|
| Purpose | Slow-varying clutter estimate for MTI subtraction |
| Implementation | `RealtimeRadarClassifier.dopp_avg`, updated `0.6·new + 0.4·history` per frame |
| State representation | Complex array `(N/2, 2M, 3)` |
| Possible states | Continuous values only — not a state machine in any control sense |
| Inputs | Current Doppler spectrum per antenna, every frame |
| Transition conditions | None (unconditional exponential update) |
| Outputs | `fft2d_mti = fft2d - dopp_avg` |
| Reset condition | Classifier construction only (zeros) — never mid-run |
| Persistence | Whole run |
| Failure concern | Stale clutter after sensor/scene moves; first frame subtracts from zeros; influences what the model sees with no visibility in the display path |

### SM-5. GUI open/stop latch (explicit UI control state)

| Field | Content |
|---|---|
| Purpose | Let the operator stop acquisition and close cleanly from the window |
| Implementation | `DetectionStatusGUI.is_open`, `stop_requested` (`patient_status_gui.py`) |
| State representation | Two booleans |
| Possible states | Open/running, stop-requested, closed (`pump()` translates close events into both flags) |
| Inputs | Stop button, window close, Escape handling, `finish()`/`close()` calls |
| Transition conditions | Button → `stop_requested`; close event → both flags; `finish()` retitles button to Close |
| Outputs | `record_frames()` breaks its loop; terminal/GUI close-out |
| Reset condition | New GUI instance per run |
| Persistence | Window lifetime |
| Failure concern | `update_status()` raises `ValueError` on any label outside the three known statuses — an unknown model output aborts the run (partial save preserved) rather than displaying |

### SM-6. NRF TX latch (downstream explicit FSM, firmware side)

| Field | Content |
|---|---|
| Purpose | Hold the authoritative obstacle state across repeated broadcasts |
| Implementation | `firmware/transceiver/src/main.c` → `tx_poll_uart()`, `tx_state` (`STATE_CLEAR`/`STATE_OBSTACLE`) |
| State representation | One latched byte |
| Possible states | `CLR`, `OBS` |
| Inputs | Exact newline-delimited `OBS`/`CLR` lines on the TX console |
| Transition conditions | Line parses to the opposite state → latch + re-advertise; anything else ignored |
| Outputs | BLE advertisement state |
| Reset condition | Boot and RX→TX entry re-initialize to `CLR` |
| Persistence | Until opposite command or reboot/role switch |
| Failure concern | None in firmware; the risk sits upstream — whatever writes serial must implement deliberate episode semantics because the latch obeys blindly |

### Proposed SM-7. Obstacle-state adapter (IMPLEMENTED)

LATCH with states `CLEAR`/`OBSTACLE` over the stabilized class (see
[`serial-integration-point.md`](serial-integration-point.md)): enter
`OBSTACLE` on stable person/robot, leave on stable nothing, hold on
unknown/error, emit wire text only on transitions. Implemented as
`integration/obstacle_state.py` → `ObstacleStateAdapter`
(`.state`, `.fault`, `.update(voted_name)` returns the new state on
transition else `None`); transport in
`integration/serial_output.py` → `SerialStateOutput` with
`last_transmitted` retry tracking. Initializes `CLEAR` with no startup
emission (matches NRF boot).

## Classification path in detail

```text
model output index (per 10-frame window)
  ↓ class_names mapping (placeholder now, detector later)
(label, score)
  ↓ appended to deque(≤5)
vote: majority count wins; ties → mean winning score
  ↓
voted label  ← final authoritative classification (GUI shows only this)
```

- One inference per 10 accumulated frames; `None` otherwise.
- One prediction object = one non-overlapping 10-frame window (~0.77 s),
  not one frame and not one person.
- The vote buffer is valid from the first prediction (no fill wait).
- Newest prediction gets no special weight; rapid alternation resolves
  by counts, then scores — symmetric, no hysteresis, flicker possible.
- Stable classification is represented only as the current voted label;
  no separate "confirmed" flag exists.
- History resets per run (new deque, cleared segments).
- Target disappears → subsequent windows vote "Nothing detected" once it
  dominates; up to ~3.9 s of stale votes linger.

## Three concepts, separated

- **A. Raw instantaneous inference**: `model(window) → index → label`.
  One window, no memory. (`_predict` return.)
- **B. Temporally stabilized classification**: voted label over ≤5
  predictions. The only defensible integration source.
  (`vote_predictions` output.)
- **C. Control/obstacle state**: `OBSTACLE` iff stable class ∈
  {person, robot}. Does not exist yet — proposed as SM-7.

Serial must attach at C, never at A (unstable per-window flips would
chatter the safety path) and never at the GUI (display layer that
rightly rejects unknown labels).

## Terminology verdicts

| Component | Correct term | Not |
|---|---|---|
| Vote deque + majority | Rolling-window temporal filter | FSM, hysteresis, latch |
| 10-frame segments | Episode accumulator / buffer | FSM |
| `dopp_avg` | Persistent numerical state (exponential clutter memory) | FSM |
| GUI open/stop flags | Explicit control state (latch-like) | — |
| NRF `tx_state` | Explicit latch FSM | — |
| Proposed adapter | Latch FSM (CLEAR/OBSTACLE) | Filter |
