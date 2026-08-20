import json
import time
from pathlib import Path
import cv2
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase


def main():
    db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    engine = AttendanceEngine(db, similarity_threshold=0.45, review_threshold=0.35, min_observations=1)
    rows = []
    for image_path in sorted(Path("dataset_1000/classrooms").glob("*.jpg")):
        image = cv2.imread(str(image_path))
        start = time.perf_counter()
        results = engine.process_frame(image, "CLASS_1000")
        elapsed = time.perf_counter() - start
        rows.append({"image": image_path.name, "faces": len(results), "seconds": elapsed,
                     "fps": 1.0 / elapsed if elapsed else 0.0})
    Path("group_size_metrics.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
