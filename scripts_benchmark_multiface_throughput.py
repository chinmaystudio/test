"""Measure optimized multi-face Render inference on a stitched classroom stress frame."""
from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import UUID, uuid5

import cv2
import numpy as np

from core.attendance_engine import AttendanceEngine
from core.batch_embedder import BatchFaceEmbedder
from db.database import LocalDatabase
from learning.prototype import calculate_prototype

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "validation_data" / "lfw"
OUT = ROOT / "validation_data" / "multiface_benchmark"
NAMESPACE = UUID("6e4a4c93-6e47-4f72-9b08-0cbdf9c1c1d4")
CLASSROOM_ID = "multiface-speed-classroom"


def aligned_embedding(engine, image):
    faces = engine.detector.detect(image)
    if not faces:
        return None
    face = max(faces, key=lambda item: float((item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1])))
    from insightface.utils.face_align import norm_crop
    crop = norm_crop(image, face.kps, image_size=112) if getattr(face, "kps", None) is not None else cv2.resize(image, (112, 112))
    return engine.batch_embedder.generate_embeddings_batch([crop], batch_size=1)[0]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    identities = []
    for identity_dir in sorted(DATASET.iterdir()):
        files = sorted(identity_dir.glob("*.jpg")) if identity_dir.is_dir() else []
        if len(files) >= 2:
            identities.append((identity_dir.name, files[:2]))
        if len(identities) == 30:
            break
    if len(identities) < 30:
        raise RuntimeError(f"Expected 30 identities, found {len(identities)}")

    cell = 220
    cols = 6
    rows = 5
    composite = np.zeros((rows * cell, cols * cell, 3), dtype=np.uint8)
    db = LocalDatabase(str(OUT / "faiss.index"), str(OUT / "metadata.json"))
    engine = AttendanceEngine(db, similarity_threshold=0.45, review_threshold=0.35, min_observations=1)
    engine.batch_embedder = BatchFaceEmbedder()

    for idx, (identity, files) in enumerate(identities):
        enrollment = cv2.imread(str(files[0]))
        embedding = aligned_embedding(engine, enrollment)
        if embedding is not None:
            db.add_embedding(calculate_prototype([embedding]), {"student_id": str(uuid5(NAMESPACE, identity)), "classroom_id": CLASSROOM_ID, "name": identity})
        image = cv2.imread(str(files[1]))
        image = cv2.resize(image, (cell - 20, cell - 20), interpolation=cv2.INTER_CUBIC)
        row, col = divmod(idx, cols)
        composite[row * cell + 10:row * cell + cell - 10, col * cell + 10:col * cell + cell - 10] = image

    composite_path = OUT / "composite_30_faces.jpg"
    cv2.imwrite(str(composite_path), composite)
    warmup_start = time.perf_counter()
    warmup_results = engine.process_frame(composite, CLASSROOM_ID, lecture_id="speed", capture_mode="manual")
    warmup_seconds = time.perf_counter() - warmup_start

    runs = []
    for _ in range(5):
        engine.reset()
        started = time.perf_counter()
        results = engine.process_frame(composite, CLASSROOM_ID, lecture_id="speed", capture_mode="manual")
        runs.append({"seconds": time.perf_counter() - started, "results": len(results)})

    report = {
        "faces_submitted": 30,
        "warmup_seconds": warmup_seconds,
        "warmup_results": len(warmup_results),
        "cold_runs": runs,
        "average_cold_seconds": float(np.mean([run["seconds"] for run in runs])),
        "p95_cold_seconds": float(np.percentile([run["seconds"] for run in runs], 95)),
        "estimated_fps": 1.0 / float(np.mean([run["seconds"] for run in runs])),
        "returned_results_average": float(np.mean([run["results"] for run in runs])),
        "embedding_batch_size": 32,
        "model": "buffalo_s",
        "provider": engine.batch_embedder.provider,
        "composite_path": str(composite_path),
        "warning": "Stitched public faces are a CPU stress test, not a real classroom accuracy claim.",
    }
    (OUT / "throughput_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
