"""Hardware-free checks for capture, placeholder outputs, and signal processing."""

import contextlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

import numpy as np

from collect_data_realtime import record_frames, vote_predictions
from patient_status_gui import DetectionStatusGUI
from realtime_classifier import PLACEHOLDER_CLASS_NAMES, RealtimeRadarClassifier


FRAME_SHAPE = (3, 4, 8)


class FakeRadar:
    def __init__(self, fail_at=None, error=None, stop_error=None):
        self.frame_count = 0
        self.fail_at = fail_at
        self.error = error
        self.stop_error = stop_error
        self.stopped = False

    def get_next_frame(self, timeout_ms):
        if self.frame_count == self.fail_at:
            raise self.error
        self.frame_count += 1
        return [np.full(FRAME_SHAPE, self.frame_count, dtype=np.float32)]

    def stop_acquisition(self):
        self.stopped = True
        if self.stop_error:
            raise self.stop_error


class FakeGUI:
    def __init__(self, stop_after=None):
        self.is_open = True
        self.stop_requested = False
        self.progress = 0
        self.statuses = []
        self.stop_after = stop_after

    def pump(self):
        if self.stop_after is not None and self.progress >= self.stop_after:
            self.stop_requested = True

    def update_progress(self, frame_count, total_frames):
        self.progress = frame_count

    def update_status(self, status):
        self.statuses.append(status)


class FakeClassifier:
    def __init__(self):
        self.count = 0

    def process_frame(self, frame):
        self.count += 1
        if self.count % 10:
            return None
        # Allow each state to dominate the rolling vote in turn.
        label = ("Person detected", "Robot detected", "Nothing detected")[
            min((self.count - 1) // 170, 2)
        ]
        return label, 0.9, np.array([0.9])


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "capture.npy"
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def capture(self, radar, **kwargs):
        return record_frames(radar, self.path, FRAME_SHAPE, **kwargs)

    def test_full_recording_saves_512_frames_and_updates_all_three_states(self):
        radar, gui = FakeRadar(), FakeGUI()
        count = self.capture(radar, realtime_classifier=FakeClassifier(), status_gui=gui)
        data = np.load(self.path)
        self.assertEqual(count, 512)
        self.assertEqual(data.shape, (512, *FRAME_SHAPE))
        self.assertEqual(data.dtype, np.complex64)
        np.testing.assert_array_equal(data[:, 0, 0, 0], np.arange(1, 513))
        self.assertEqual(gui.progress, 512)
        self.assertEqual(len(gui.statuses), 51)
        self.assertEqual(set(gui.statuses), set(DetectionStatusGUI.STATUS_COLORS))
        self.assertEqual(gui.statuses[-1], "Nothing detected")
        self.assertTrue(radar.stopped)

    def test_stop_button_saves_only_frames_already_received(self):
        radar = FakeRadar()
        self.assertEqual(self.capture(radar, status_gui=FakeGUI(stop_after=13)), 13)
        self.assertEqual(np.load(self.path).shape[0], 13)
        self.assertTrue(radar.stopped)

    def test_closed_gui_does_not_start_capture_or_save_an_empty_file(self):
        radar, gui = FakeRadar(), FakeGUI()
        gui.is_open = False
        self.assertEqual(self.capture(radar, status_gui=gui), 0)
        self.assertFalse(self.path.exists())
        self.assertTrue(radar.stopped)

    def test_keyboard_interrupt_saves_partial_recording(self):
        radar = FakeRadar(fail_at=7, error=KeyboardInterrupt())
        self.assertEqual(self.capture(radar), 7)
        self.assertEqual(np.load(self.path).shape[0], 7)
        self.assertTrue(radar.stopped)

    def test_read_error_propagates_after_partial_recording_is_saved(self):
        radar = FakeRadar(fail_at=4, error=RuntimeError("radar disconnected"))
        with self.assertRaisesRegex(RuntimeError, "radar disconnected"):
            self.capture(radar)
        self.assertEqual(np.load(self.path).shape[0], 4)
        self.assertTrue(radar.stopped)

    def test_inference_error_preserves_the_frame_that_triggered_it(self):
        classifier = SimpleNamespace(
            process_frame=MagicMock(side_effect=RuntimeError("inference failed"))
        )
        radar = FakeRadar()
        with self.assertRaisesRegex(RuntimeError, "inference failed"):
            self.capture(radar, realtime_classifier=classifier)
        self.assertEqual(np.load(self.path).shape[0], 1)
        self.assertTrue(radar.stopped)

    def test_stop_error_does_not_prevent_saving(self):
        radar = FakeRadar(stop_error=RuntimeError("stop failed"))
        with self.assertRaisesRegex(RuntimeError, "stop failed"):
            self.capture(radar, num_frames=3)
        self.assertEqual(np.load(self.path).shape[0], 3)

    def test_first_prediction_does_not_wait_for_five_votes(self):
        gui = FakeGUI()
        self.capture(FakeRadar(), num_frames=10, realtime_classifier=FakeClassifier(), status_gui=gui)
        self.assertEqual(gui.statuses, ["Person detected"])


class PredictionTests(unittest.TestCase):
    def test_label_vote_uses_count_then_average_score(self):
        self.assertEqual(vote_predictions([
            ("Person detected", 0.6), ("Robot detected", 0.99), ("Person detected", 0.7),
        ])[0], "Person detected")
        self.assertEqual(vote_predictions([
            ("Person detected", 0.6), ("Robot detected", 0.8),
        ])[0], "Robot detected")

    def test_every_legacy_output_is_adapted_to_a_supported_detection(self):
        classifier = RealtimeRadarClassifier.__new__(RealtimeRadarClassifier)
        classifier.class_names = PLACEHOLDER_CLASS_NAMES
        inputs = [np.zeros((10, 32, 256), dtype=np.float32)] * 2
        for index in range(7):
            probabilities = np.eye(7, dtype=np.float32)[index]
            classifier.model = SimpleNamespace(predict=lambda *args, **kwargs: probabilities[None])
            name, score, actual = classifier._predict(inputs)
            self.assertIn(name, DetectionStatusGUI.STATUS_COLORS)
            self.assertEqual(name, PLACEHOLDER_CLASS_NAMES[index])
            self.assertEqual(score, 1.0)
            np.testing.assert_array_equal(actual, probabilities)

    def test_windowing_emits_predictions_every_ten_frames(self):
        classifier = RealtimeRadarClassifier.__new__(RealtimeRadarClassifier)
        classifier.window_frames = 10
        classifier.elevation_segment = []
        classifier.doppler_segment = []
        classifier._make_maps = lambda frame: (frame, frame)
        classifier._predict = MagicMock(return_value=("Robot detected", 0.9, np.array([0.9])))
        for index in range(21):
            result = classifier.process_frame(np.full((2, 3), index))
            self.assertEqual(result is not None, (index + 1) % 10 == 0)
        self.assertEqual(classifier._predict.call_count, 2)
        second_inputs = classifier._predict.call_args.args[0]
        np.testing.assert_array_equal(second_inputs[0][:, 0, 0], np.arange(10, 20))
        self.assertEqual(len(classifier.elevation_segment), 1)

    def test_warm_up_does_not_consume_or_modify_real_frame_buffers(self):
        classifier = RealtimeRadarClassifier.__new__(RealtimeRadarClassifier)
        classifier.window_frames = 10
        classifier.target_shape = (32, 256)
        classifier.elevation_segment = []
        classifier.doppler_segment = []
        classifier._predict = MagicMock()
        classifier.warm_up()
        self.assertEqual(classifier.elevation_segment, [])
        self.assertEqual(classifier.doppler_segment, [])
        for data in classifier._predict.call_args.args[0]:
            self.assertEqual(data.shape, (10, 32, 256))
            self.assertFalse(np.any(data))

    def test_batched_capon_matches_original_calculation(self):
        classifier = RealtimeRadarClassifier.__new__(RealtimeRadarClassifier)
        classifier.num_chirps = 8
        rng = np.random.default_rng(42)
        steering_vector = np.exp(-1j * np.pi * np.sin(np.linspace(-np.pi / 2, np.pi / 2, 16)))
        for profiles in (
            rng.normal(size=(2, 4, 16)) + 1j * rng.normal(size=(2, 4, 16)),
            np.zeros((2, 4, 16), dtype=complex),
        ):
            moved = np.moveaxis(profiles, 0, -1)
            hermitian = np.conjugate(moved.transpose(0, 2, 1)) / classifier.num_chirps
            expected = np.zeros((4, 16), dtype=complex)
            for row in range(4):
                inverse = np.linalg.pinv(hermitian[row] @ moved[row])
                for col, angle in enumerate(steering_vector):
                    steering = np.array([1, angle])
                    denominator = steering.conjugate().T @ inverse @ steering
                    expected[row, col] = 0 if denominator == 0 else 1 / denominator
            np.testing.assert_allclose(
                classifier._capon_map(profiles, steering_vector), expected, rtol=1e-11, atol=1e-12
            )

    def test_completion_does_not_replace_last_detection(self):
        gui = DetectionStatusGUI.__new__(DetectionStatusGUI)
        gui.is_open = True
        gui.status_text = MagicMock()
        gui.result_detail = MagicMock()
        gui.recording_text = MagicMock()
        gui.stop_button = MagicMock()
        gui.update_status("Robot detected")
        gui.status_text.configure.reset_mock()
        gui.finish("Collection complete - 512 / 512 frames saved")
        gui.status_text.configure.assert_not_called()
        gui.recording_text.configure.assert_called_with(
            text="Collection complete - 512 / 512 frames saved"
        )
        with self.assertRaises(ValueError):
            gui.update_status("Collection complete")


if __name__ == "__main__":
    unittest.main()
