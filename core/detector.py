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
        """
        Detect faces in an image.
        Returns a list of face objects containing bbox, kps, det_score.
        """
        faces = self.app.get(img)
        return faces

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
