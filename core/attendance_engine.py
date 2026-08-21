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

    def process_frame(self, frame, classroom_id: str, lecture_id: str = "default", capture_mode: str = "live") -> list[dict]:
        """Process a frame using server-side detection and ArcFace matching.

        Live preview uses temporal confirmation to suppress one-frame false positives.
        A teacher-triggered manual capture uses the same similarity policy but confirms
        a high-confidence match from that captured frame immediately.
        """
        manual_capture = capture_mode.lower() == "manual"
        if manual_capture:
            # Do not let low-confidence preview history block a fresh teacher capture.
            self.temporal.clear()
            self.track_identities.clear()
        faces = self.detector.detect(frame)
        tracked_faces = self.tracker.update(faces)
        results = []
        # Prepare batch processing
        valid_faces = []
        valid_crops = []
        valid_track_ids = []
        
        # Throttle embeddings for stable tracks
        # For a 70-face frame, we only need to re-embed if the track is new, 
        # hasn't reached temporal stability, or a refresh interval has passed.
        
        for track_id, face in tracked_faces:
            # Check if we can skip embedding this frame for this track
            skip_embedding = False
            if track_id in self.track_identities:
                # If we already confirmed this identity and it's stable, we can skip
                # expensive embedding on every frame. (In production, use a frame counter).
                skip_embedding = True
                
            quality = self.quality.check(frame, face)
            if not quality.accepted:
                results.append({"track_id": track_id, "student_id": None, "name": None,
                                "similarity": 0.0, "status": "UNKNOWN", "confidence": "LOW",
                                "verification": "REVIEW", "reason": quality.reason,
                                "bbox": face.bbox.tolist()})
                continue
                
            # Use tracker bounding box for crop
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            h, w = frame.shape[:2]
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
                
            import cv2
            try:
                from insightface.utils.face_align import norm_crop
                if getattr(face, 'kps', None) is not None:
                    crop_resized = norm_crop(frame, face.kps, image_size=112)
                else:
                    crop_resized = cv2.resize(crop, (112, 112))
            except Exception:
                crop_resized = cv2.resize(crop, (112, 112))
            
            if skip_embedding:
                # Use cached identity state
                student_id, name, conf = self.track_identities[track_id]
                results.append({
                    "track_id": track_id,
                    "student_id": student_id,
                    "name": name,
                    "similarity": round(float(conf), 4),
                    "status": "PRESENT",
                    "confidence": "HIGH",
                    "verification": "AUTO",
                    "observations": self.temporal.min_observations,
                    "already_confirmed": True,
                    "bbox": face.bbox.tolist(),
                })
            else:
                valid_faces.append(face)
                valid_crops.append(crop_resized)
                valid_track_ids.append(track_id)
            
        if not valid_crops:
            return results
            
        # Batch inference (much faster for 70 faces)
        from core.batch_embedder import BatchFaceEmbedder
        if not hasattr(self, 'batch_embedder'):
            self.batch_embedder = BatchFaceEmbedder()
            
        embeddings = self.batch_embedder.generate_embeddings_batch(valid_crops, batch_size=32)
        
        # Batch search
        matches_list = self.db.search_batch(embeddings, k=2, classroom_id=classroom_id)
        
        for i, (track_id, face, embedding, matches) in enumerate(zip(valid_track_ids, valid_faces, embeddings, matches_list)):
            # Create margin from second best if available
            best_match = matches[0] if matches else None
            second_best = matches[1] if len(matches) > 1 else None
            margin = (best_match['similarity'] if best_match else 0.0) - (second_best['similarity'] if second_best else 0.0)
            
            # Pass full match dict so policy can extract what it needs
            if best_match:
                best_match['margin'] = margin
                
            decision = self.policy.decide(best_match)
            temporal = self.temporal.observe(track_id, decision.student_id, decision.name, decision.similarity, min_observations=1 if manual_capture else None)
            status = "PRESENT" if temporal.confirmed and decision.state is MatchState.HIGH_CONFIDENCE else "REVIEW"
            verification = "AUTO" if status == "PRESENT" else "MANUAL"
            if temporal.confirmed and decision.state is MatchState.HIGH_CONFIDENCE:
                self.confirmed.add(f"{classroom_id}:{lecture_id}:{temporal.student_id}")
                self.track_identities[track_id] = (temporal.student_id, temporal.name, temporal.confidence)

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
