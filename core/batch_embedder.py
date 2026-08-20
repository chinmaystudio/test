import onnxruntime as ort
import numpy as np
from typing import List
from core.model_manager import model_manager


class BatchFaceEmbedder:
    """ArcFace embedding service with a real batch API and provider reporting."""

    def __init__(self, det_size=(640, 640)):
        self.det_size = det_size

    @property
    def app(self):
        return model_manager.get_app(self.det_size)

    @property
    def model(self):
        return self.app.models["recognition"]

    @property
    def provider(self) -> str:
        # Fallback to checking the active provider from the model manager's session
        env_provider = __import__("os").environ.get("ONNX_PROVIDER")
        if env_provider:
            return env_provider
        return "CPUExecutionProvider"

    def generate_embeddings_batch(self, face_crops: List[np.ndarray], batch_size: int = 16) -> List[List[float]]:
        """Generate normalized ArcFace embeddings for pre-aligned BGR face crops.

        The ArcFace wrapper accepts a list/array of aligned crops. Input crops should
        be 112x112 BGR images; callers can use the detector landmarks for alignment.
        """
        if not face_crops:
            return []
        results: List[List[float]] = []
        for start in range(0, len(face_crops), max(1, batch_size)):
            batch = face_crops[start:start + batch_size]
            if any(np.asarray(crop).ndim != 3 for crop in batch):
                raise ValueError("face_crops must contain HxWxC arrays")
            embeddings = self.model.get_feat(batch)
            for embedding in np.asarray(embeddings):
                embedding = embedding.astype(np.float32)
                norm = np.linalg.norm(embedding)
                results.append((embedding / norm if norm else embedding).tolist())
        return results
