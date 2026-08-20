import onnxruntime as ort
import numpy as np
from typing import List
from insightface.app import FaceAnalysis


class BatchFaceEmbedder:
    """ArcFace embedding service with a real batch API and provider reporting."""

    def __init__(self, det_size=(640, 640)):
        providers = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
        available_providers = ort.get_available_providers()
        selected_providers = [p for p in providers if p in available_providers]
        if not selected_providers:
            raise RuntimeError("No ONNX Runtime execution provider is available")
        self.providers = selected_providers
        self.app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"], providers=selected_providers)
        self.app.prepare(ctx_id=0, det_size=det_size)
        self.model = self.app.models["recognition"]

    @property
    def provider(self) -> str:
        return self.providers[0]

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
