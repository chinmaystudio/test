import numpy as np
from core.model_manager import model_manager

class FaceEmbedder:
    def __init__(self, det_size=(640, 640)):
        self.det_size = det_size

    @property
    def app(self):
        return model_manager.get_app(self.det_size)

    def generate_embedding(self, img, face):
        """
        Generate embedding for a specific detected face.
        insightface app.get() actually does detection and recognition if modules are loaded.
        Here we assume face is already detected and we just want its embedding,
        or we pass the image and let it process.
        For simplicity, we process the image and find the closest face to the given bbox.
        """
        faces = self.app.get(img)
        if not faces:
            return None

        # Match face by bbox center
        target_center = ((face.bbox[0] + face.bbox[2])/2, (face.bbox[1] + face.bbox[3])/2)
        best_face = None
        min_dist = float('inf')

        for f in faces:
            center = ((f.bbox[0] + f.bbox[2])/2, (f.bbox[1] + f.bbox[3])/2)
            dist = (center[0] - target_center[0])**2 + (center[1] - target_center[1])**2
            if dist < min_dist:
                min_dist = dist
                best_face = f

        if best_face and hasattr(best_face, 'embedding'):
            # Normalize embedding
            emb = best_face.embedding
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            return emb

        return None
