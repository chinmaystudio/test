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
    for width in (640, 960, 1280, 1920, 2560, 3840):
        scale = width / image.shape[1]
        resized = cv2.resize(image, (width, max(1, int(image.shape[0] * scale))))
        start = time.perf_counter()
        faces = detector.detect(resized)
        elapsed = time.perf_counter() - start
        rows.append({"width": width, "height": resized.shape[0], "faces_detected": len(faces),
                     "seconds": elapsed, "fps": 1.0 / elapsed if elapsed else 0.0})
    Path("resolution_metrics.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
