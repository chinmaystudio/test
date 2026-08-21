from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass
class TemporalDecision:
    student_id: Optional[str]
    name: Optional[str]
    confidence: float
    observations: int
    confirmed: bool


class TemporalVerifier:
    def __init__(self, min_observations: int = 5, window_size: int = 12, stability_delta: float = 0.08):
        self.min_observations = min_observations
        self.window_size = window_size
        self.stability_delta = stability_delta
        self.history: Dict[int, Deque[dict]] = defaultdict(lambda: deque(maxlen=window_size))

    def observe(self, track_id: int, student_id: Optional[str], name: Optional[str], similarity: float, min_observations: Optional[int] = None) -> TemporalDecision:
        self.history[track_id].append({"student_id": student_id, "name": name, "similarity": float(similarity)})
        observations = list(self.history[track_id])
        by_identity: Dict[Optional[str], list] = defaultdict(list)
        for item in observations:
            by_identity[item["student_id"]].append(item["similarity"])
        identity, scores = max(by_identity.items(), key=lambda pair: len(pair[1]))
        avg = sum(scores) / len(scores) if scores else 0.0
        required_observations = self.min_observations if min_observations is None else max(1, int(min_observations))
        stable = len(scores) >= required_observations and (max(scores) - min(scores) <= self.stability_delta)
        confirmed = identity is not None and stable
        name_value = next((i["name"] for i in reversed(observations) if i["student_id"] == identity), None)
        return TemporalDecision(identity if confirmed else None, name_value if confirmed else None,
                                avg, len(scores), confirmed)

    def clear(self, track_id: Optional[int] = None) -> None:
        if track_id is None:
            self.history.clear()
        else:
            self.history.pop(track_id, None)
