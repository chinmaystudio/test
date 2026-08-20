from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List
import statistics


@dataclass
class DriftAlert:
    student_id: str
    metric: str
    baseline: float
    current: float
    message: str


class DriftMonitor:
    def __init__(self, similarity_drop_threshold: float = 0.10):
        self.similarity_drop_threshold = similarity_drop_threshold
        self.history: Dict[str, List[float]] = defaultdict(list)

    def record_similarity(self, student_id: str, similarity: float) -> None:
        self.history[student_id].append(float(similarity))

    def alerts(self) -> List[DriftAlert]:
        alerts = []
        for student_id, values in self.history.items():
            if len(values) < 4:
                continue
            baseline = statistics.mean(values[: max(2, len(values) // 3)])
            current = statistics.mean(values[-max(2, len(values) // 3):])
            if baseline - current >= self.similarity_drop_threshold:
                alerts.append(DriftAlert(student_id, "average_similarity", baseline, current,
                                         "Recognition similarity has materially declined; review camera, appearance, or profile updates."))
        return alerts
