from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class QualityResult:
    accepted: bool
    score: float
    reason: Optional[str] = None


def assess_face_quality(image: np.ndarray, bbox, detection_score: float, min_size: int = 40,
                        min_detection_score: float = 0.60, min_blur_score: float = 40.0) -> QualityResult:
    """Reject faces that are too small, weakly detected, or severely blurred."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = image.shape[:2]
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    width, height = x2 - x1, y2 - y1
    if width < min_size or height < min_size:
        return QualityResult(False, 0.0, "face_too_small")
    if float(detection_score) < min_detection_score:
        return QualityResult(False, float(detection_score), "low_detection_score")
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return QualityResult(False, 0.0, "empty_crop")
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < min_blur_score:
        return QualityResult(False, min(1.0, blur_score / min_blur_score), "too_blurry")
    return QualityResult(True, min(1.0, blur_score / (min_blur_score * 5.0)), None)


class FaceQualityChecker:
    def __init__(self, min_size: int = 40, min_detection_score: float = 0.60, min_blur_score: float = 40.0):
        self.min_size = min_size
        self.min_detection_score = min_detection_score
        self.min_blur_score = min_blur_score

    def check(self, image: np.ndarray, face) -> QualityResult:
        return assess_face_quality(image, face.bbox, face.det_score, self.min_size,
                                   self.min_detection_score, self.min_blur_score)



