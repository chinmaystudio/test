import json
import time
from pathlib import Path
import cv2
from core.detector import FaceDetector


def main():
    detector = FaceDetector()
    image_path = next(Path("dataset_1000/classrooms").glob("*.jpg"), None)
    if image_path is None:
        raise FileNotFoundError("Generate classroom scenes first")
    image = cv2.imread(str(image_path))
    rows = []
    for target_size in (40, 60, 80, 100, 150, 200):
        # Controlled resize approximating the target face scale while keeping the full scene.
        scale = target_size / 100.0
        resized = cv2.resize(image, None, fx=scale, fy=scale)
        start = time.perf_counter()
        faces = detector.detect(resized)
        elapsed = time.perf_counter() - start
        rows.append({"approx_face_size": target_size, "faces_detected": len(faces),
                     "seconds": elapsed})
    Path("small_face_metrics.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
