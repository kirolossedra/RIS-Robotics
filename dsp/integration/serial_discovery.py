"""Automatic nRF/J-Link serial discovery (read-only, never transmits).

Identifies the NRF Transceiver TX console from ``pyserial`` USB metadata
on Windows and Linux. Identification uses metadata only — never port-name
patterns (``COM14``, ``/dev/ttyACM0`` are outcomes, not criteria) — and
never sends bytes: a silent TX console is valid and must not be rejected.

Physical-board grouping comes first: one Nordic/J-Link board may expose
several CDC interfaces, and they must not be mistaken for several boards.
Auto-selection happens only when exactly one board exists and its UART
interface is determinable; otherwise the result is ``None`` (serial
disabled, DSP continues).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

# Metadata tokens identifying Nordic/SEGGER/J-Link/DAPLink interfaces.
# Deliberately excludes bare "usb serial": generic USB-UART adapters share
# that description without being Nordic hardware (observed on lab machines).
_CANDIDATE_TOKENS = (
    "j-link",
    "jlink",
    "segger",
    "nrf",
    "nordic",
    "cmsis-dap",
)

# SEGGER USB vendor ID (observed on both lab boards as VID 1366).
_SEGGER_VID = 0x1366


@dataclass(frozen=True)
class SerialInterface:
    device: str
    description: str = ""
    manufacturer: str = ""
    product: str = ""
    serial_number: str = ""
    location: str = ""
    interface: str = ""
    hwid: str = ""
    vid: Optional[int] = None
    pid: Optional[int] = None


@dataclass(frozen=True)
class NrfBoard:
    identity: str
    interfaces: tuple = field(default_factory=tuple)


def _text(info) -> str:
    parts = [
        getattr(info, "description", ""),
        getattr(info, "manufacturer", ""),
        getattr(info, "product", ""),
        getattr(info, "interface", ""),
        getattr(info, "hwid", ""),
        getattr(info, "device", ""),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _is_candidate(info) -> bool:
    text = _text(info)
    if any(token in text for token in _CANDIDATE_TOKENS):
        return True
    try:
        return info.vid is not None and int(info.vid) == _SEGGER_VID
    except (TypeError, ValueError):
        return False


def _board_key(info) -> tuple:
    """Identity shared by all interfaces of one physical board."""
    serial_number = getattr(info, "serial_number", "") or ""
    if serial_number:
        return ("sn", str(serial_number))
    location = getattr(info, "location", "") or ""
    if location:
        return ("loc", str(location))
    hwid = getattr(info, "hwid", "") or ""
    if hwid:
        # Interfaces of one board differ only by the MI_xx part.
        normalized = re.sub(r"MI_\d+", "MI_", hwid, flags=re.IGNORECASE)
        return ("hwid", normalized)
    return ("dev", str(getattr(info, "device", "") or ""))


def _interface_key(info) -> tuple:
    """Deterministic intra-board order: lowest USB interface first."""
    hwid = getattr(info, "hwid", "") or ""
    match = re.search(r"MI_(\d+)", hwid, re.IGNORECASE)
    if match:
        return (0, int(match.group(1)), "")
    interface = getattr(info, "interface", "") or ""
    match = re.search(r"(\d+)", interface)
    if match:
        return (1, int(match.group(1)), "")
    return (2, 0, str(getattr(info, "device", "") or ""))


def _to_interface(info) -> SerialInterface:
    return SerialInterface(
        device=str(getattr(info, "device", "") or ""),
        description=str(getattr(info, "description", "") or ""),
        manufacturer=str(getattr(info, "manufacturer", "") or ""),
        product=str(getattr(info, "product", "") or ""),
        serial_number=str(getattr(info, "serial_number", "") or ""),
        location=str(getattr(info, "location", "") or ""),
        interface=str(getattr(info, "interface", "") or ""),
        hwid=str(getattr(info, "hwid", "") or ""),
        vid=getattr(info, "vid", None),
        pid=getattr(info, "pid", None),
    )


def find_nrf_boards(port_infos=None) -> List[NrfBoard]:
    """Group candidate nRF/J-Link interfaces by physical board.

    Never raises: enumeration errors yield an empty list (serial
    disabled upstream). Never transmits.
    """
    if port_infos is None:
        try:
            from serial.tools import list_ports

            port_infos = list(list_ports.comports())
        except Exception:
            return []
    grouped: dict = {}
    for info in port_infos or []:
        try:
            if not _is_candidate(info):
                continue
            key = _board_key(info)
        except Exception:
            continue
        grouped.setdefault(key, []).append(info)
    boards = []
    for key, infos in grouped.items():
        ordered = sorted(infos, key=_interface_key)
        boards.append(
            NrfBoard(
                identity=":".join(key),
                interfaces=tuple(_to_interface(i) for i in ordered),
            )
        )
    boards.sort(key=lambda board: board.identity)
    return boards


def discover_nrf_serial_port(port_infos=None) -> Optional[str]:
    """Return the TX console device path, or None when not unambiguous.

    Selection rule: exactly one physical board, and (for multi-interface
    boards) its lowest-numbered CDC interface — the DK target-UART
    convention (MI_00) observed on the lab boards' working TX/RX links.
    Anything else (none, several boards) yields None.
    """
    boards = find_nrf_boards(port_infos)
    if len(boards) != 1:
        return None
    interfaces = boards[0].interfaces
    if not interfaces:
        return None
    return interfaces[0].device or None
