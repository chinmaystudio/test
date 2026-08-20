from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional
import time


class LearningState(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATING = "VALIDATING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class ObservationCandidate:
    observation_id: str
    student_id: Optional[str]
    classroom_id: str
    session_id: str
    embedding: List[float]
    similarity: float
    second_best_similarity: float
    margin: float
    face_quality: float
    liveness_score: float
    track_id: int
    timestamp: float
    state: LearningState = LearningState.CANDIDATE
    rejection_reason: Optional[str] = None


class ObservationQueue:
    def __init__(self, max_pending: int = 1000):
        self.max_pending = max_pending
        self.pending: List[ObservationCandidate] = []

    def add(self, candidate: ObservationCandidate) -> None:
        if len(self.pending) >= self.max_pending:
            self.pending.pop(0)
        candidate.state = LearningState.VALIDATING
        self.pending.append(candidate)

    def finalize(self, observation_id: str, state: LearningState, reason: Optional[str] = None) -> Optional[ObservationCandidate]:
        for candidate in self.pending:
            if candidate.observation_id == observation_id:
                candidate.state = state
                candidate.rejection_reason = reason
                self.pending.remove(candidate)
                return candidate
        return None

    def list_pending(self) -> List[dict]:
        return [asdict(item) for item in self.pending]
