"""Hardware-free checks for the obstacle-state FSM and serial output."""

import contextlib
import io
import unittest

from integration.obstacle_state import (
    CLEAR_LABEL,
    OBSTACLE_LABELS,
    ObstacleState,
    ObstacleStateAdapter,
)
from integration.serial_output import BAUD, SerialStateOutput


class FakeStream:
    def __init__(self, fail_on_write=False):
        self.written = []
        self.flushed = 0
        self.closed = False
        self.fail_on_write = fail_on_write

    def write(self, data):
        if self.fail_on_write:
            raise IOError("port gone")
        self.written.append(bytes(data))

    def flush(self):
        self.flushed += 1

    def close(self):
        self.closed = True


def make_writer(stream=None):
    return SerialStateOutput("COM9", stream=FakeStream() if stream is None else stream)


class ObstacleStateTests(unittest.TestCase):
    def test_initial_state_is_clear_and_silent(self):
        adapter = ObstacleStateAdapter()
        self.assertEqual(adapter.state, ObstacleState.CLEAR)
        self.assertIsNone(adapter.fault)
        for _ in range(3):
            self.assertIsNone(adapter.update("Nothing detected"))
        self.assertEqual(adapter.state, ObstacleState.CLEAR)

    def test_enter_obstacle_on_person_or_robot(self):
        for label in ("Person detected", "Robot detected"):
            adapter = ObstacleStateAdapter()
            self.assertEqual(adapter.update(label), ObstacleState.OBSTACLE)
            self.assertEqual(adapter.state, ObstacleState.OBSTACLE)
            self.assertIsNone(adapter.fault)

    def test_persistent_obstacle_emits_nothing(self):
        adapter = ObstacleStateAdapter()
        adapter.update("Person detected")
        for label in ("Person detected", "Robot detected", "Robot detected"):
            self.assertIsNone(adapter.update(label))
            self.assertEqual(adapter.state, ObstacleState.OBSTACLE)

    def test_clear_obstacle_on_nothing(self):
        adapter = ObstacleStateAdapter()
        adapter.update("Robot detected")
        self.assertEqual(adapter.update("Nothing detected"), ObstacleState.CLEAR)
        self.assertEqual(adapter.state, ObstacleState.CLEAR)

    def test_unknown_holds_state_and_records_fault(self):
        adapter = ObstacleStateAdapter()
        self.assertIsNone(adapter.update("Unknown class: 7"))
        self.assertEqual(adapter.state, ObstacleState.CLEAR)
        self.assertIsNotNone(adapter.fault)
        adapter.update("Person detected")
        self.assertEqual(adapter.state, ObstacleState.OBSTACLE)
        self.assertIsNone(adapter.fault)
        self.assertIsNone(adapter.update("mystery"))
        self.assertEqual(adapter.state, ObstacleState.OBSTACLE)
        self.assertIsNotNone(adapter.fault)

    def test_episode_produces_single_obs_then_clr(self):
        adapter = ObstacleStateAdapter()
        transitions = []
        for label in ["Nothing", "Nothing", "Person detected", "Person detected",
                      "Robot detected", "Robot detected", "Nothing detected",
                      "Nothing detected"]:
            if label == "Nothing":
                label = "Nothing detected"
            result = adapter.update(label)
            if result is not None:
                transitions.append(result)
        self.assertEqual(transitions, [ObstacleState.OBSTACLE, ObstacleState.CLEAR])

    def test_mapping_comes_from_classifier_contract(self):
        self.assertEqual(OBSTACLE_LABELS, {"Person detected", "Robot detected"})
        self.assertEqual(CLEAR_LABEL, "Nothing detected")


class SerialOutputTests(unittest.TestCase):
    def test_transitions_render_exact_framing(self):
        writer = make_writer()
        self.assertTrue(writer.send(ObstacleState.OBSTACLE))
        self.assertTrue(writer.send(ObstacleState.CLEAR))
        self.assertEqual(writer._stream.written, [b"OBS\n", b"CLR\n"])

    def test_default_baud_matches_nrf_tx(self):
        self.assertEqual(BAUD, 115200)
        self.assertEqual(make_writer().baud, 115200)

    def test_sync_is_transition_only(self):
        writer = make_writer()
        self.assertTrue(writer.sync(ObstacleState.CLEAR))
        self.assertEqual(writer._stream.written, [])
        self.assertTrue(writer.sync(ObstacleState.OBSTACLE))
        self.assertTrue(writer.sync(ObstacleState.OBSTACLE))
        self.assertEqual(writer._stream.written, [b"OBS\n"])
        self.assertTrue(writer.sync(ObstacleState.CLEAR))
        self.assertEqual(writer._stream.written, [b"OBS\n", b"CLR\n"])

    def test_write_failure_surfaced_and_retried(self):
        stream = FakeStream(fail_on_write=True)
        writer = make_writer(stream)
        self.assertFalse(writer.sync(ObstacleState.OBSTACLE))
        self.assertIsNotNone(writer.last_error)
        self.assertEqual(writer.last_transmitted, ObstacleState.CLEAR)
        self.assertEqual(stream.written, [])
        stream.fail_on_write = False
        self.assertTrue(writer.sync(ObstacleState.OBSTACLE))
        self.assertEqual(stream.written, [b"OBS\n"])
        self.assertEqual(writer.last_transmitted, ObstacleState.OBSTACLE)

    def test_close_is_quiet_and_idempotent(self):
        stream = FakeStream()
        writer = make_writer(stream)
        writer.close()
        self.assertTrue(stream.closed)
        self.assertEqual(stream.written, [])
        writer.close()

    def test_open_failure_without_pyserial(self):
        import builtins
        real_import = builtins.__import__

        def no_serial(name, *args, **kwargs):
            if name == "serial":
                raise ImportError("No module named 'serial'")
            return real_import(name, *args, **kwargs)

        writer = SerialStateOutput("COM9")
        builtins.__import__ = no_serial
        try:
            with self.assertRaisesRegex(RuntimeError, "pyserial"):
                writer.open()
        finally:
            builtins.__import__ = real_import


class WiringTests(unittest.TestCase):
    def test_cli_defaults_leave_serial_to_discovery(self):
        from collect_data_realtime import parse_args

        args = parse_args([])
        self.assertFalse(hasattr(args, "serial_port"))
        self.assertEqual(args.serial_baud, 115200)
        self.assertFalse(args.serial_allow_placeholder)

    def test_record_frames_drives_writer_through_adapter(self):
        import tempfile
        from pathlib import Path

        import numpy as np
        from collect_data_realtime import record_frames

        class Device:
            def get_next_frame(self, timeout_ms):
                return [np.zeros((1, 1, 1))]

            def stop_acquisition(self):
                pass

        class Classifier:
            def __init__(self):
                self.labels = ["Person detected"] * 2 + ["Nothing detected"] * 2

            def process_frame(self, frame):
                return (self.labels.pop(0), 0.9, np.array([0.9]))

        stream = FakeStream()
        writer = SerialStateOutput("COM9", stream=stream)
        adapter = ObstacleStateAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "capture.npy")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                record_frames(Device(), path, (1, 1, 1), num_frames=1,
                              realtime_classifier=Classifier(), serial_writer=writer,
                              obstacle_adapter=adapter)
        # One prediction per frame here: Person -> OBS written once.
        self.assertEqual(stream.written, [b"OBS\n"])
        self.assertEqual(adapter.state, ObstacleState.OBSTACLE)


if __name__ == "__main__":
    unittest.main()
