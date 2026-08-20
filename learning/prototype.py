import numpy as np
from typing import List


def calculate_prototype(embeddings: List[List[float]], method: str = "centroid") -> List[float]:
    """Calculate the representative embedding prototype."""
    if not embeddings:
        raise ValueError("Cannot calculate prototype from empty list")
    arr = np.array(embeddings, dtype=np.float32)
    
    if method == "centroid":
        proto = np.mean(arr, axis=0)
    elif method == "medoid":
        # Find embedding with minimum average distance to all others
        dists = np.dot(arr, arr.T) # Cosine similarity since vectors are normalized
        avg_sims = np.mean(dists, axis=1)
        proto = arr[np.argmax(avg_sims)]
    else:
        proto = np.mean(arr, axis=0)
        
    norm = np.linalg.norm(proto)
    if norm > 0:
        proto = proto / norm
    return proto.tolist()


def is_outlier(embedding: List[float], profile_embeddings: List[List[float]], min_similarity: float = 0.50) -> bool:
    """Check if an embedding is an outlier compared to the existing profile distribution."""
    if not profile_embeddings:
        return False
    arr = np.array(profile_embeddings, dtype=np.float32)
    emb = np.array(embedding, dtype=np.float32)
    sims = np.dot(arr, emb)
    # If the max similarity to existing embeddings is below threshold, it's an outlier
    return float(np.max(sims)) < min_similarity


def is_novel(embedding: List[float], profile_embeddings: List[List[float]], novelty_threshold: float = 0.85) -> bool:
    """Check if an embedding provides new information (is not too similar to existing ones)."""
    if not profile_embeddings:
        return True
    arr = np.array(profile_embeddings, dtype=np.float32)
    emb = np.array(embedding, dtype=np.float32)
    sims = np.dot(arr, emb)
    # If it's highly similar to any existing embedding, it's not novel
    return float(np.max(sims)) < novelty_threshold
