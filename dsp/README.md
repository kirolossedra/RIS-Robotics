# RIS Corner real-time radar detection

Run from this folder using the existing Python environment:

```powershell
.\.venv_tf\Scripts\python.exe .\collect_data_realtime.py
```

Press Enter when the radar and subject are ready. The script records **512 frames
at 12.94 Hz** (about 39.6 seconds) and saves the raw capture as a NumPy array with
shape `(frames, rx, chirps, samples)` and dtype `complex64`.

The GUI displays **Person detected**, **Robot detected**, or **Nothing detected**.
It shows a dash until the first prediction is available, with recording progress
below the result. The existing model needs 10-frame windows, so a result is
available every 10 frames (about 0.77 seconds at the configured acquisition rate).
A rolling vote over the latest five predictions smooths the display; it starts
with the first prediction without waiting for all five. Ties use the average
winning-output score. Each result describes recent frames, rather than an
independent classification of each individual frame.

Click **Stop recording**, close the window, or press Ctrl+C in the terminal to
stop early. Frames already collected are saved without unused buffer entries.
The last result remains visible when a recording finishes; click **Close** to exit.
Acquisition/inference errors also save frames already captured, then report the
error in the terminal.

## Placeholder model

`Bathroom_CNNLSTM.keras` is retained unchanged and loaded from this folder.
It is an activity classifier, **not a trained person/robot/empty-scene detector**.
The GUI and terminal explicitly mark placeholder mode. Its temporary mapping is:

| Existing model output index | GUI result |
| --- | --- |
| 0 | Person detected |
| 1 | Robot detected |
| 2, 3, 4, 5, 6 | Nothing detected |

These assignments only exercise the interface. In particular, "Nothing detected"
in placeholder mode does not establish that the scene is empty. No detection
accuracy is implied, and the terminal's model score refers to the winning
original model output.

The adapter in `realtime_classifier.py` keeps the current preprocessing:
range-elevation and range-Doppler maps, resized to `(32, 256)`, buffered into
10-frame windows, and normalized per timestep. The Capon calculation is batched
to reduce processing overhead while retaining the same calculation.
Model inference is warmed up before acquisition starts to avoid a startup pause
while radar frames are arriving.

To use a trained detector with the same two-input format, set
`CLASSIFICATION_MODEL_PATH` to its file, adjust `DETECTION_CLASS_NAMES` to match
its output order, and set `PLACEHOLDER_MODE = False`. The default target order is
`0 = person`, `1 = robot`, `2 = nothing`. Output mapping coverage is checked when
loading the model. A model with different inputs also needs adapter changes.

## Settings

Settings are at the top of `collect_data_realtime.py`:

- `FILE_NAME` and `SAVE_FOLDER`: capture destination. The existing default is
  `C:\Users\j3visser\Documents\RIS\Test_LOS_realtime.npy`; subsequent recordings
  replace that file, so change the name when keeping multiple captures.
- `NUM_FRAMES` and `FRAME_RATE`: recording length and acquisition rate.
- `ENABLE_REALTIME_CLASSIFICATION`: turn inference on or off.
- `CLASSIFICATION_WINDOW_FRAMES`: keep at 10 for the supplied model.
- `VOTE_WINDOW_PREDICTIONS`: number of recent predictions used for smoothing.
- `SHOW_DETECTION_STATUS_GUI`, `LOCATION_LABEL`, and `SHOW_LIVE_PLOT`: display options.
- `CLASSIFICATION_MODEL_PATH` and `PLACEHOLDER_MODE`: model configuration.

The radar SDK, NumPy, Matplotlib, Keras, TensorFlow, and Tkinter must be available
in the Python environment. Keras/TensorFlow dependencies are listed in
`requirements.txt`; the radar SDK is provided separately by the parent SDK folder.

Run the automated checks without connecting a radar:

```powershell
.\.venv_tf\Scripts\python.exe -m unittest discover -s tests -v
```
