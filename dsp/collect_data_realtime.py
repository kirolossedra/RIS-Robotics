import argparse
import time
from collections import Counter, deque
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ifxradarsdk import get_version_full
from ifxradarsdk.fmcw import DeviceFmcw
from ifxradarsdk.fmcw.types import FmcwMetrics, FmcwSimpleSequenceConfig

from integration.obstacle_state import ObstacleStateAdapter
from integration.serial_output import BAUD, SerialStateOutput
from patient_status_gui import DetectionStatusGUI
from realtime_classifier import (
    DETECTION_CLASS_NAMES,
    PLACEHOLDER_CLASS_NAMES,
    RealtimeRadarClassifier,
)


# =========================
# USER SETTINGS
# =========================

FILE_NAME = "Test_LOS_realtime.npy"
SAVE_FOLDER = Path(r"C:\Users\j3visser\Documents\RIS")
SAVE_PATH = SAVE_FOLDER / FILE_NAME

NUM_FRAMES = 512
FRAME_RATE = 12.94
SHOW_LIVE_PLOT = False
BIN_IDX = 1

ENABLE_REALTIME_CLASSIFICATION = True
CLASSIFICATION_WINDOW_FRAMES = 10
VOTE_WINDOW_PREDICTIONS = 5
SHOW_DETECTION_STATUS_GUI = True
LOCATION_LABEL = "RIS Corner"
# Keep True until the model and output mapping are replaced with a trained detector.
PLACEHOLDER_MODE = True
CLASSIFICATION_MODEL_PATH = Path(__file__).resolve().parent / "Bathroom_CNNLSTM.keras"

SERIAL_BAUD = BAUD


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="RIS Corner real-time radar detection. "
        "Serial NRF output requires --serial-port and is refused "
        "under placeholder inference without --serial-allow-placeholder."
    )
    parser.add_argument("--serial-port", default=None,
                        help="NRF TX console device, e.g. COM14 or /dev/ttyACM0. "
                        "Absent: DSP + display run with serial disabled.")
    parser.add_argument("--serial-baud", type=int, default=SERIAL_BAUD,
                        help="Serial baud rate (default: 115200 for NRF TX).")
    parser.add_argument("--serial-allow-placeholder", action="store_true",
                        help="DEVELOPMENT ONLY: permit serial output while "
                        "PLACEHOLDER_MODE is on, for integration testing "
                        "without the trained model. Never use in experiments.")
    return parser.parse_args(argv)


# =========================
# LIVE PLOT
# =========================

class LivePlot:
    def __init__(self, frame_rate):
        plt.ion()
        self.frame_rate = frame_rate
        self.time = []
        self.mag = []

        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.line, = self.ax.plot([], [], label="Average RX Bin 1 Magnitude")

        self.ax.set_title("Live Bin 1 Magnitude")
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Magnitude")
        self.ax.grid(True)
        self.ax.legend()

        self.is_open = True
        self.fig.canvas.mpl_connect("close_event", self.close)

    def update(self, frame_idx, value):
        if not self.is_open:
            return

        t = frame_idx / self.frame_rate
        self.time.append(t)
        self.mag.append(value)

        self.line.set_data(self.time, self.mag)
        self.ax.relim()
        self.ax.autoscale_view()

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def close(self, event=None):
        self.is_open = False
        plt.close(self.fig)


def compute_live_bin_mag(frame_data, bin_idx=1):
    num_rx, _, num_samples = frame_data.shape
    window = np.hanning(num_samples)

    mags = []
    for rx in range(num_rx):
        chirp_data = frame_data[rx, 0, :].astype(float)
        chirp_data = chirp_data - np.mean(chirp_data)
        chirp_data = chirp_data * window

        fft_result = np.fft.fft(chirp_data)
        mags.append(np.abs(fft_result[bin_idx]))

    return np.mean(mags)


def vote_predictions(predictions):
    """Vote by detection label; resolve ties by average winning-output score."""
    counts = Counter(name for name, _ in predictions)
    top_count = max(counts.values())
    tied_names = [name for name, count in counts.items() if count == top_count]
    voted_name = max(
        tied_names,
        key=lambda name: np.mean([score for label, score in predictions if label == name]),
    )
    voted_score = float(np.mean([score for name, score in predictions if name == voted_name]))
    return voted_name, voted_score, top_count


def record_frames(
    device, save_path, frame_shape, num_frames=NUM_FRAMES,
    realtime_classifier=None, status_gui=None, live_plot=None,
    vote_window=VOTE_WINDOW_PREDICTIONS,
    serial_writer=None, obstacle_adapter=None,
):
    """Capture a bounded recording and save only acquired frames, including on stop/error."""
    if num_frames < 1 or vote_window < 1:
        raise ValueError("Frame count and vote window must be positive.")
    collected_data = np.empty((num_frames, *frame_shape), dtype=np.complex64)
    prediction_votes = deque(maxlen=vote_window)
    frame_count = 0
    started = time.perf_counter()
    print("Output shape:", collected_data.shape)
    print("Output dtype:", collected_data.dtype)
    print("\nRecording...\n")
    try:
        while frame_count < num_frames:
            if status_gui is not None:
                status_gui.pump()
                if status_gui.stop_requested or not status_gui.is_open:
                    break

            frame_data = device.get_next_frame(timeout_ms=1000)[0]
            collected_data[frame_count] = frame_data
            frame_count += 1

            if live_plot is not None:
                live_plot.update(frame_count - 1, compute_live_bin_mag(frame_data, BIN_IDX))

            if realtime_classifier is not None:
                prediction = realtime_classifier.process_frame(frame_data)
                if prediction is not None:
                    class_name, confidence, _ = prediction
                    prediction_votes.append((class_name, confidence))
                    voted_name, voted_score, vote_count = vote_predictions(prediction_votes)
                    if obstacle_adapter is not None:
                        obstacle_adapter.update(voted_name)
                        if obstacle_adapter.fault is not None:
                            print(f"\nIntegration fault: {obstacle_adapter.fault}")
                        if serial_writer is not None and not serial_writer.sync(
                            obstacle_adapter.state
                        ):
                            print(f"\n{serial_writer.last_error}")
                    print(
                        f"\n{voted_name} "
                        f"({vote_count}/{len(prediction_votes)} votes, "
                        f"model score {voted_score:.1%})"
                    )
                    if status_gui is not None:
                        status_gui.update_status(voted_name)

            if status_gui is not None:
                status_gui.update_progress(frame_count, num_frames)
            print(f"Frame {frame_count}/{num_frames}", end="\r")
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
    finally:
        elapsed = time.perf_counter() - started
        # Stop hardware even if the user closes the window or inference fails.
        # Saving still runs if the SDK reports an error while stopping.
        try:
            device.stop_acquisition()
        finally:
            if frame_count:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(save_path, collected_data[:frame_count])
                print(f"\nSaved {frame_count} frames to:\n{save_path}")
            else:
                print("\nNo frames collected; no file saved.")
            print(f"Elapsed recording time: {elapsed:.2f} s")
    return frame_count


# =========================
# MAIN SCRIPT
# =========================

def main(argv=None):
    args = parse_args(argv)
    print("\n==========================================")
    print("RIS Corner - Realtime Person / Robot Detection")
    print("==========================================")
    print(f"Save file: {SAVE_PATH}")
    print(f"Frames: {NUM_FRAMES}")
    print(f"Frame rate: {FRAME_RATE} Hz")
    print(f"Recorded time: {NUM_FRAMES / FRAME_RATE:.1f} s")
    if ENABLE_REALTIME_CLASSIFICATION:
        print(f"Model: {CLASSIFICATION_MODEL_PATH}")
        if PLACEHOLDER_MODE:
            print("PLACEHOLDER MODE: temporary labels for UI testing, not trained detections.")
    else:
        print("Classification disabled; recording raw radar data only.")
    if args.serial_port is None:
        print("Serial NRF output: disabled (no --serial-port).")
    elif PLACEHOLDER_MODE and not args.serial_allow_placeholder:
        print("ERROR: refusing serial output under placeholder inference. "
              "Train/replace the detector (PLACEHOLDER_MODE = False) or pass "
              "--serial-allow-placeholder for development-only testing.")
        return 2
    else:
        print(f"Serial NRF output: {args.serial_port} at {args.serial_baud} baud"
              + (" (DEVELOPMENT placeholder override)" if PLACEHOLDER_MODE else ""))
    print("==========================================\n")

    input("Place radar / subject, then press ENTER to start...")

    obstacle_adapter = ObstacleStateAdapter() if args.serial_port else None
    serial_writer = None
    if args.serial_port:
        serial_writer = SerialStateOutput(args.serial_port, args.serial_baud)
        try:
            serial_writer.open()
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
            return 2

    status_gui = None
    live_plot = None
    try:
        with DeviceFmcw() as device:
            print(f"Radar SDK Version: {get_version_full()}")
            print("Sensor:", device.get_sensor_type())

            num_rx_antennas = device.get_sensor_information()["num_rx_antennas"]

            metrics = FmcwMetrics(
                range_resolution_m=0.05,
                max_range_m=1.6,
                max_speed_m_s=2.0,
                speed_resolution_m_s=0.065,
                center_frequency_Hz=60_750_000_000,
            )

            sequence = device.create_simple_sequence(FmcwSimpleSequenceConfig())
            sequence.loop.repetition_time_s = 1 / FRAME_RATE

            chirp_loop = sequence.loop.sub_sequence.contents
            device.sequence_from_metrics(metrics, chirp_loop)

            chirp = chirp_loop.loop.sub_sequence.contents.chirp
            chirp.start_frequency_Hz = 59_250_000_000
            chirp.end_frequency_Hz = 62_250_000_000
            chirp.sample_rate_Hz = 2_000_000
            chirp.rx_mask = (1 << num_rx_antennas) - 1
            chirp.tx_mask = 1
            chirp.tx_power_level = 31
            chirp.if_gain_dB = 23
            chirp.lp_cutoff_Hz = 500_000
            chirp.hp_cutoff_Hz = 80_000

            device.set_acquisition_sequence(sequence)

            num_chirps = chirp_loop.loop.num_repetitions
            num_samples = chirp.num_samples

            print("\nAcquisition config:")
            print("RX antennas:", num_rx_antennas)
            print("Chirps/frame:", num_chirps)
            print("Samples/chirp:", num_samples)
            print("Frame rate:", FRAME_RATE)
            print("Start freq:", chirp.start_frequency_Hz)
            print("End freq:", chirp.end_frequency_Hz)
            print("Sample rate:", chirp.sample_rate_Hz)
            print("IF gain:", chirp.if_gain_dB)
            print("HP cutoff:", chirp.hp_cutoff_Hz)
            print("LP cutoff:", chirp.lp_cutoff_Hz)

            if ENABLE_REALTIME_CLASSIFICATION:
                realtime_classifier = RealtimeRadarClassifier(
                    CLASSIFICATION_MODEL_PATH,
                    num_rx_antennas,
                    num_chirps,
                    num_samples,
                    CLASSIFICATION_WINDOW_FRAMES,
                    class_names=(
                        PLACEHOLDER_CLASS_NAMES if PLACEHOLDER_MODE else DETECTION_CLASS_NAMES
                    ),
                )
                realtime_classifier.warm_up()
                print("Realtime classifier loaded and ready.")
            else:
                realtime_classifier = None

            live_plot = LivePlot(FRAME_RATE) if SHOW_LIVE_PLOT else None
            status_gui = (
                DetectionStatusGUI(LOCATION_LABEL, placeholder_mode=PLACEHOLDER_MODE)
                if SHOW_DETECTION_STATUS_GUI else None
            )
            if status_gui is not None and realtime_classifier is None:
                status_gui.result_detail.configure(text="Classification disabled")

            frame_count = record_frames(
                device, SAVE_PATH, (num_rx_antennas, num_chirps, num_samples),
                num_frames=NUM_FRAMES, realtime_classifier=realtime_classifier,
                status_gui=status_gui, live_plot=live_plot,
                serial_writer=serial_writer, obstacle_adapter=obstacle_adapter,
            )

        completion = "Collection complete" if frame_count == NUM_FRAMES else "Recording stopped"
        completion += f" - {frame_count} / {NUM_FRAMES} frames"
        if frame_count:
            completion += " saved"
        print(completion)
        if status_gui is not None:
            status_gui.finish(completion)
            status_gui.pump()
            status_gui.wait_until_closed()
        if live_plot is not None:
            plt.ioff()
            plt.show()
    finally:
        if status_gui is not None:
            status_gui.close()
        if live_plot is not None:
            live_plot.close()
        if serial_writer is not None:
            serial_writer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
