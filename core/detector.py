import cv2
import numpy as np
from insightface.app import FaceAnalysis

import onnxruntime as ort

class FaceDetector:
    def __init__(self, det_size=(640, 640)):
        providers = ['CUDAExecutionProvider', 'TensorrtExecutionProvider', 'CPUExecutionProvider']
        available_providers = ort.get_available_providers()
        selected_providers = [p for p in providers if p in available_providers]

        self.app = FaceAnalysis(name='buffalo_l', allowed_modules=['detection', 'landmark_2d_106'], providers=selected_providers)
        self.app.prepare(ctx_id=0, det_size=det_size)

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
