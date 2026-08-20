from typing import List, Dict, Optional
import time

from db.profiles import ProfileStore, IdentityProfile
from learning.prototype import calculate_prototype, is_outlier, is_novel
from db.database import LocalDatabase


class ProfileManager:
    def __init__(self, profile_store: ProfileStore, vector_db: LocalDatabase, 
                 max_profile_size: int = 50, novelty_threshold: float = 0.85, 
                 outlier_threshold: float = 0.50):
        self.store = profile_store
        self.vector_db = vector_db
        self.max_profile_size = max_profile_size
        self.novelty_threshold = novelty_threshold
        self.outlier_threshold = outlier_threshold

    def create_initial_profile(self, student_id: str, classroom_id: str, enrollment_embeddings: List[List[float]]) -> IdentityProfile:
        proto = calculate_prototype(enrollment_embeddings, method="centroid")
        profile = IdentityProfile(
            student_id=student_id,
            classroom_id=classroom_id,
            enrollment_embeddings=enrollment_embeddings,
            prototype_embedding=proto,
            profile_version=1
        )
        self.store.save_profile(profile, reason="initial_enrollment")
        
        # Add prototype to vector DB for fast matching
        self.vector_db.add_embedding(proto, {
            "student_id": student_id,
            "classroom_id": classroom_id,
            "is_prototype": True
        })
        return profile

    def queue_observation(self, student_id: str, embedding: List[float], confidence: str, margin: float):
        """Process a candidate observation for potential learning."""
        if confidence != "HIGH":
            return {"status": "REJECTED", "reason": "low_confidence"}
            
        if margin < 0.15: # Prevent multiple-identity consistency issues
            return {"status": "REVIEW_REQUIRED", "reason": "ambiguous_match"}
            
        profile = self.store.get_profile(student_id)
        if not profile:
            return {"status": "REJECTED", "reason": "profile_not_found"}
            
        all_embs = profile.get_all_embeddings()
        
        if is_outlier(embedding, all_embs, self.outlier_threshold):
            return {"status": "REVIEW_REQUIRED", "reason": "outlier"}
            
        if not is_novel(embedding, all_embs, self.novelty_threshold):
            return {"status": "REJECTED", "reason": "redundant"}
            
        # Accept observation
        profile.verified_embeddings.append(embedding)
        
        # Compress if too large
        if len(profile.verified_embeddings) > self.max_profile_size:
            # Simple compression: keep newest. Production should use clustering.
            profile.verified_embeddings = profile.verified_embeddings[-self.max_profile_size:]
            
        # Update prototype
        profile.prototype_embedding = calculate_prototype(profile.get_all_embeddings(), method="centroid")
        profile.profile_version += 1
        profile.last_updated = time.time()
        
        self.store.save_profile(profile, reason="continual_learning")
        
        # Update vector DB with new prototype (in production, we'd remove the old one or rebuild index)
        # For MVP, we just add the new prototype.
        self.vector_db.add_embedding(profile.prototype_embedding, {
            "student_id": student_id,
            "classroom_id": profile.classroom_id,
            "is_prototype": True,
            "version": profile.profile_version
        })
        
        return {"status": "ACCEPTED", "reason": "profile_updated", "version": profile.profile_version}
