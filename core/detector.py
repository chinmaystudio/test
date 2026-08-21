import cv2
import numpy as np
from core.model_manager import model_manager

class FaceDetector:
    def __init__(self, det_size=(640, 640)):
        self.det_size = det_size

    @property
    def app(self):
        return model_manager.get_app(self.det_size)

    def detect(self, img):
        """Detect faces, retrying once on an upscaled frame for small classroom faces."""
        if img is None:
            return []
        faces = self.app.get(img)
        if faces:
            return faces
        height, width = img.shape[:2]
        if max(height, width) >= 1280:
            return faces
        import cv2
        scale = min(2.0, 1280.0 / max(height, width))
        enlarged = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_CUBIC)
        enlarged_faces = self.app.get(enlarged)
        for face in enlarged_faces:
            face.bbox = np.asarray(face.bbox, dtype=np.float32) / scale
            if getattr(face, 'kps', None) is not None:
                face.kps = np.asarray(face.kps, dtype=np.float32) / scale
        return enlarged_faces

    def check_quality(self, face, min_size=40, min_score=0.6):
        """
        Basic quality check for enrollment.
        """
        bbox = face.bbox
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        if width < min_size or height < min_size:
            return False, "Face too small"

        if face.det_score < min_score:
            return False, "Detection confidence too low"

        return True, "Good"
