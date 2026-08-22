from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MatchState(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNKNOWN = "UNKNOWN"


@dataclass
class MatchDecision:
    student_id: Optional[str]
    name: Optional[str]
    similarity: float
    state: MatchState


class ThresholdPolicy:
    """Thresholds should be calibrated on held-out genuine and impostor data."""
    def __init__(self, auto_threshold: float = 0.55, review_threshold: float = 0.45):
        if not 0 <= review_threshold <= auto_threshold <= 1:
            raise ValueError("Expected 0 <= review_threshold <= auto_threshold <= 1")
        self.auto_threshold = auto_threshold
        self.review_threshold = review_threshold

    def decide(self, match: Optional[dict]) -> MatchDecision:
        if not match:
            return MatchDecision(None, None, 0.0, MatchState.UNKNOWN)
        similarity = max(0.0, min(1.0, float(match.get("similarity", 0.0))))
        if similarity >= self.auto_threshold:
            state = MatchState.HIGH_CONFIDENCE
        elif similarity >= self.review_threshold:
            state = MatchState.LOW_CONFIDENCE
        else:
            state = MatchState.UNKNOWN
        # Always return the best candidate's identity so the UI and temporal tracker
        # know who is being reviewed, even if confidence is currently UNKNOWN/LOW.
        return MatchDecision(match.get("student_id"), match.get("name"), similarity, state)
