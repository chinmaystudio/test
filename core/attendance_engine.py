from __future__ import annotations

from typing import Dict, Set

from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from core.liveness import LivenessChecker
from core.matching import ThresholdPolicy, MatchState
from core.quality import FaceQualityChecker
from core.temporal import TemporalVerifier
from core.tracker import SimpleTracker
from db.database import LocalDatabase


class AttendanceEngine:
    """Stateful group-attendance processor for one classroom session."""

    def __init__(self, db: LocalDatabase, similarity_threshold: float = 0.55,
                 review_threshold: float = 0.45, min_observations: int = 5):
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.quality = FaceQualityChecker()
        self.tracker = SimpleTracker()
        self.temporal = TemporalVerifier(min_observations=min_observations)
        self.policy = ThresholdPolicy(similarity_threshold, review_threshold)
        self.liveness = LivenessChecker(enabled=False)
        self.db = db
        self.confirmed: Set[str] = set()
        self.track_identities: Dict[int, str] = {}

    def reset(self) -> None:
        self.tracker = SimpleTracker()
        self.temporal.clear()
        self.confirmed.clear()
        self.track_identities.clear()

    def process_frame(self, frame, classroom_id: str, lecture_id: str = "default") -> list[dict]:
        faces = self.detector.detect(frame)
        tracked_faces = self.tracker.update(faces)
        results = []
        for track_id, face in tracked_faces:
            quality = self.quality.check(frame, face)
            if not quality.accepted:
                results.append({"track_id": track_id, "student_id": None, "name": None,
                                "similarity": 0.0, "status": "UNKNOWN", "confidence": "LOW",
                                "verification": "REVIEW", "reason": quality.reason,
                                "bbox": face.bbox.tolist()})
                continue

            embedding = self.embedder.generate_embedding(frame, face)
            match = self.db.search(embedding, k=1, classroom_id=classroom_id) if embedding is not None else []
            decision = self.policy.decide(match[0] if match else None)
            temporal = self.temporal.observe(track_id, decision.student_id, decision.name, decision.similarity)
            status = "PRESENT" if temporal.confirmed and decision.state is MatchState.HIGH_CONFIDENCE else "REVIEW"
            verification = "AUTO" if status == "PRESENT" else "MANUAL"
            if temporal.confirmed and decision.state is MatchState.HIGH_CONFIDENCE:
                self.confirmed.add(f"{classroom_id}:{lecture_id}:{temporal.student_id}")

                # Continual learning queue hook (simulated integration)
                # In production, this would call ProfileManager.queue_observation asynchronously
                # using the margin (decision.similarity - second_best_similarity) and the embedding.

            results.append({
                "track_id": track_id,
                "student_id": temporal.student_id or decision.student_id,
                "name": temporal.name or decision.name,
                "similarity": round(float(temporal.confidence), 4),
                "status": status,
                "confidence": "HIGH" if status == "PRESENT" else ("MEDIUM" if decision.state is MatchState.LOW_CONFIDENCE else "LOW"),
                "verification": verification,
                "observations": temporal.observations,
                "already_confirmed": f"{classroom_id}:{lecture_id}:{temporal.student_id}" in self.confirmed if temporal.student_id else False,
                "bbox": face.bbox.tolist(),
            })
        return results
