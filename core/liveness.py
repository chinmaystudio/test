from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class LivenessResult:
    is_live: bool
    score: float
    method: str


class LivenessChecker:
    """MVP hook; replace with a trained anti-spoofing model before production use."""
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def check_liveness(self, face_sequence: Sequence[np.ndarray]) -> LivenessResult:
        if not self.enabled:
            return LivenessResult(True, 0.0, "disabled_mvp_hook")
        if not face_sequence:
            return LivenessResult(False, 0.0, "no_frames")
        # Deliberately conservative placeholder. It never claims a real liveness guarantee.
        return LivenessResult(False, 0.0, "not_implemented")
