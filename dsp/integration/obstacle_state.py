"""Semantic obstacle-state latch between stable classification and serial output.

The rolling vote produces display labels; this adapter owns the
control-relevant question only: is an obstacle (person or robot)
currently observed? Internal states are CLEAR/OBSTACLE and never wire
strings — rendering to ``CLR``/``OBS`` belongs to the serial layer.

Unknown or invalid labels must never clear the state: sensing silence
is not evidence of a clear corridor.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from realtime_classifier import DETECTION_CLASS_NAMES


class ObstacleState(Enum):
    CLEAR = "CLEAR"
    OBSTACLE = "OBSTACLE"


# Semantic labels from the established classifier contract
# (DETECTION_CLASS_NAMES: 0 = person, 1 = robot, 2 = nothing).
OBSTACLE_LABELS = frozenset(
    {DETECTION_CLASS_NAMES[0], DETECTION_CLASS_NAMES[1]}
)
CLEAR_LABEL = DETECTION_CLASS_NAMES[2]


class ObstacleStateAdapter:
    """Two-state latch over voted classification labels.

    Initial state is CLEAR, matching NRF Transceiver TX boot state, and
    no transition is emitted for it: the first serial output happens
    only on a real CLEAR -> OBSTACLE change.
    """

    def __init__(self) -> None:
        self.state = ObstacleState.CLEAR
        self.fault: Optional[str] = None

    def update(self, voted_name: str) -> Optional[ObstacleState]:
        """Feed one stabilized (voted) label.

        Returns the new state on a transition, else None. Unknown labels
        hold the current state and record a fault instead.
        """
        if voted_name in OBSTACLE_LABELS:
            desired = ObstacleState.OBSTACLE
        elif voted_name == CLEAR_LABEL:
            desired = ObstacleState.CLEAR
        else:
            self.fault = f"unmapped classification label: {voted_name!r}"
            return None

        self.fault = None
        if desired == self.state:
            return None
        self.state = desired
        return desired
