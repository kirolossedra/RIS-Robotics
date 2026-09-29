"""Hardware-free checks for nRF/J-Link serial discovery."""

import contextlib
import io
import unittest
from types import SimpleNamespace

from integration.serial_discovery import (
    discover_nrf_serial_port,
    find_nrf_boards,
)


def port(device, description="", manufacturer="", product="",
         serial_number="", location="", interface="", hwid="",
         vid=None, pid=None):
    return SimpleNamespace(
        device=device, description=description, manufacturer=manufacturer,
        product=product, serial_number=serial_number, location=location,
        interface=interface, hwid=hwid, vid=vid, pid=pid,
    )


def jlink(device, serial, mi="00"):
    return port(device,
                description="JLink CDC UART Port",
                manufacturer="SEGGER",
                hwid=f"USB\\VID_1366&PID_1061&MI_{mi}\\6&XYZ&0&000{mi}",
                serial_number=serial, vid=0x1366, pid=0x1061)


class DiscoveryTests(unittest.TestCase):
    def test_single_clear_candidate_selected(self):
        ports = [jlink("COM14", "1050670813", "00"),
                 jlink("COM13", "1050670813", "02")]
        self.assertEqual(discover_nrf_serial_port(ports), "COM14")

    def test_no_serial_ports_yields_none(self):
        self.assertEqual(discover_nrf_serial_port([]), None)
        self.assertEqual(find_nrf_boards([]), [])

    def test_unrelated_devices_never_selected(self):
        ports = [
            port("COM3", description="USB Serial Device",
                 manufacturer="FTDI", hwid="USB\\VID_0403&PID_6001\\X",
                 vid=0x0403, pid=0x6001),
            port("/dev/ttyUSB0", description="USB-Serial Controller",
                 manufacturer="Prolific"),
            port("COM9", description="Bluetooth Link"),
        ]
        self.assertEqual(discover_nrf_serial_port(ports), None)

    def test_two_physical_boards_is_ambiguous(self):
        ports = [jlink("COM8", "1050670813", "00"),
                 jlink("COM14", "1050611489", "00")]
        self.assertEqual(len(find_nrf_boards(ports)), 2)
        self.assertIsNone(discover_nrf_serial_port(ports))

    def test_interfaces_grouped_by_serial_number(self):
        ports = [jlink("COM14", "1050670813", "00"),
                 jlink("COM13", "1050670813", "02")]
        boards = find_nrf_boards(ports)
        self.assertEqual(len(boards), 1)
        self.assertEqual([i.device for i in boards[0].interfaces],
                         ["COM14", "COM13"])

    def test_missing_serial_falls_back_to_location(self):
        ports = [
            port("/dev/ttyACM0", description="J-Link OB",
                 manufacturer="SEGGER", location="1-2.3",
                 hwid="USB VID:PID=1366:0101 LOCATION=1-2.3"),
            port("/dev/ttyACM1", description="J-Link OB",
                 manufacturer="SEGGER", location="1-2.3",
                 hwid="USB VID:PID=1366:0101 LOCATION=1-2.3"),
        ]
        boards = find_nrf_boards(ports)
        self.assertEqual(len(boards), 1)
        self.assertEqual(discover_nrf_serial_port(ports), "/dev/ttyACM0")

    def test_single_interface_board_selected(self):
        ports = [jlink("COM8", "1050670813", "00")]
        self.assertEqual(discover_nrf_serial_port(ports), "COM8")

    def test_case_insensitive_tokens(self):
        variants = [
            ("SEGGER J-Link", "Segger"),
            ("segger jlink", "SEGGER"),
            ("J-LINK CDC", "x"),
            ("j-link", "y"),
            ("Nordic nRF DK", "z"),
            ("nRF52833", "w"),
            ("CMSIS-DAP probe", "v"),
        ]
        for description, manufacturer in variants:
            with self.subTest(description=description):
                ports = [port("COM5", description=description,
                              manufacturer=manufacturer, serial_number="S1")]
                self.assertEqual(discover_nrf_serial_port(ports), "COM5")

    def test_segger_vid_alone_identifies(self):
        ports = [port("COM5", description="CDC UART Port",
                      serial_number="S9", vid=0x1366)]
        self.assertEqual(discover_nrf_serial_port(ports), "COM5")

    def test_missing_metadata_never_crashes(self):
        ports = [port("COM5"), port(None), SimpleNamespace()]
        self.assertIsNone(discover_nrf_serial_port(ports))

    def test_enumeration_exception_yields_no_boards(self):
        import serial.tools.list_ports as list_ports

        real = list_ports.comports

        def boom():
            raise OSError("enumeration failed")

        list_ports.comports = boom
        try:
            self.assertEqual(find_nrf_boards(), [])
            self.assertIsNone(discover_nrf_serial_port())
        finally:
            list_ports.comports = real


class ApplicationContinuityTests(unittest.TestCase):
    def test_failed_discovery_leaves_dsp_path_operational(self):
        import tempfile
        from pathlib import Path

        import numpy as np
        from collect_data_realtime import record_frames
        from integration.serial_discovery import find_nrf_boards

        self.assertEqual(find_nrf_boards([]), [])

        class Device:
            def get_next_frame(self, timeout_ms):
                return [np.zeros((1, 1, 1))]

            def stop_acquisition(self):
                pass

        class Classifier:
            def process_frame(self, frame):
                return ("Person detected", 0.9, np.array([0.9]))

        class Gui:
            is_open = True
            stop_requested = False
            statuses = []

            def pump(self):
                pass

            def update_progress(self, *args):
                pass

            def update_status(self, status):
                self.statuses.append(status)

        gui = Gui()
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                count = record_frames(
                    Device(), str(Path(tmp) / "capture.npy"), (1, 1, 1),
                    num_frames=2, realtime_classifier=Classifier(),
                    status_gui=gui, serial_writer=None, obstacle_adapter=None)
        # Classification, GUI updates, and recording proceed with no writer.
        self.assertEqual(count, 2)
        self.assertEqual(gui.statuses, ["Person detected", "Person detected"])


if __name__ == "__main__":
    unittest.main()
