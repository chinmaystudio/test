from dataclasses import dataclass


@dataclass
class AdaptationPolicy:
    enabled: bool = True
    min_similarity: float = 0.75
    min_margin: float = 0.15
    min_quality: float = 0.60
    min_liveness: float = 0.50
    min_observations: int = 3
    max_new_embeddings_per_session: int = 3
    min_embedding_distance: float = 0.15

    def validate(self, similarity: float, margin: float, quality: float, liveness: float,
                 observations: int) -> tuple[bool, str]:
        if not self.enabled:
            return False, "adaptation_disabled"
        if similarity < self.min_similarity:
            return False, "low_similarity"
        if margin < self.min_margin:
            return False, "ambiguous_margin"
        if quality < self.min_quality:
            return False, "poor_quality"
        if liveness < self.min_liveness:
            return False, "failed_liveness"
        if observations < self.min_observations:
            return False, "insufficient_temporal_observations"
        return True, "accepted_by_policy"
