"""Storage-neutral 1,000-identity ArcFace benchmark for NeuroClass.

The benchmark uses public LFW images as an engineering stress test. It enrolls
one centroid vector per identity, evaluates a held-out image for each genuine
identity, evaluates an equal-sized unknown/impostor set, and sweeps thresholds.
It does not claim classroom accuracy or demographic parity.
"""
from __future__ import annotations

import gc
import json
import random
import time
from pathlib import Path
from uuid import UUID, uuid5

import cv2
import numpy as np
import psutil

from core.attendance_engine import AttendanceEngine
from core.batch_embedder import BatchFaceEmbedder
from db.database import LocalDatabase
from learning.prototype import calculate_prototype

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "validation_data" / "lfw"
OUT = ROOT / "validation_data" / "benchmark_1000"
CLASSROOM_ID = "benchmark-classroom-1000"
NAMESPACE = UUID("c9c4b48a-a92e-4d8b-bf21-a3d3c83aef4a")


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


def choose_identities(required: int = 2000) -> list[tuple[str, list[Path]]]:
    candidates = []
    for identity_dir in DATASET.iterdir():
        if not identity_dir.is_dir():
            continue
        files = sorted(identity_dir.glob("*.jpg"))
        if len(files) >= 2:
            candidates.append((identity_dir.name, files))
    random.Random(1000).shuffle(candidates)
    if len(candidates) < required:
        raise RuntimeError(f"Need {required} identities with two images; found {len(candidates)}")
    return candidates[:required]


def extract_embedding(engine: AttendanceEngine, image: np.ndarray):
    if image is None:
        return None
    faces = engine.detector.detect(image)
    if not faces:
        return None
    face = max(faces, key=lambda item: float((item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1])))
    try:
        from insightface.utils.face_align import norm_crop
        crop = norm_crop(image, face.kps, image_size=112) if getattr(face, "kps", None) is not None else None
    except Exception:
        crop = None
    if crop is None:
        x1, y1, x2, y2 = [int(value) for value in face.bbox]
        crop = image[max(0, y1):max(y1 + 1, y2), max(0, x1):max(x1 + 1, x2)]
        if crop.size == 0:
            return None
        crop = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)
    return np.asarray(engine.batch_embedder.generate_embeddings_batch([crop], batch_size=1)[0], dtype=np.float32)


def evaluate(scores: list[dict], threshold: float) -> dict:
    tp = sum(row["expected"] is not None and row["best_id"] == row["expected"] and row["score"] >= threshold for row in scores)
    fn = sum(row["expected"] is not None and not (row["best_id"] == row["expected"] and row["score"] >= threshold) for row in scores)
    fp = sum(row["expected"] is None and row["best_id"] is not None and row["score"] >= threshold for row in scores)
    tn = sum(row["expected"] is None and not (row["best_id"] is not None and row["score"] >= threshold) for row in scores)
    genuine = tp + fn
    unknown = fp + tn
    return {
        "threshold": threshold,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "recognition_accuracy": tp / genuine if genuine else 0.0,
        "false_rejection_rate": fn / genuine if genuine else 0.0,
        "false_acceptance_rate": fp / unknown if unknown else 0.0,
        "balanced_accuracy": ((tp / genuine if genuine else 0.0) + (tn / unknown if unknown else 0.0)) / 2,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    selected = choose_identities(1680)
    registered = selected[:1000]
    unknown = selected[1000:]
    db = LocalDatabase(str(OUT / "faiss.index"), str(OUT / "metadata.json"))
    engine = AttendanceEngine(db, similarity_threshold=0.55, review_threshold=0.45, min_observations=1)
    engine.batch_embedder = BatchFaceEmbedder()
    baseline_rss = rss_mb()

    enrollment_failures = []
    enrollment_counts = []
    for identity, files in registered:
        student_id = str(uuid5(NAMESPACE, identity))
        embeddings = []
        for enrollment_path in files[: min(3, len(files) - 1)]:
            embedding = extract_embedding(engine, cv2.imread(str(enrollment_path)))
            if embedding is not None:
                embeddings.append(embedding.tolist())
        if not embeddings:
            enrollment_failures.append(identity)
            continue
        prototype = calculate_prototype(embeddings, method="centroid")
        db.add_embedding(prototype, {"student_id": student_id, "classroom_id": CLASSROOM_ID, "name": identity, "sample_count": len(embeddings), "profile_type": "centroid"})
        enrollment_counts.append(len(embeddings))

    scores = []
    latency_ms = []
    for expected_group, should_match in ((registered, True), (unknown, False)):
        for identity, files in expected_group:
            capture_path = files[-1]
            started = time.perf_counter()
            embedding = extract_embedding(engine, cv2.imread(str(capture_path)))
            latency_ms.append((time.perf_counter() - started) * 1000)
            best_id = None
            best_score = 0.0
            if embedding is not None:
                matches = db.search(embedding.tolist(), k=1, classroom_id=CLASSROOM_ID)
                if matches:
                    best_id = matches[0].get("student_id")
                    best_score = float(matches[0].get("similarity", 0.0))
            scores.append({
                "identity": identity,
                "expected": str(uuid5(NAMESPACE, identity)) if should_match else None,
                "best_id": best_id,
                "score": best_score,
                "detected": embedding is not None,
            })

    threshold_rows = [evaluate(scores, round(value, 2)) for value in np.arange(0.35, 0.701, 0.01)]
    zero_far = [row for row in threshold_rows if row["false_acceptance_rate"] == 0.0]
    selected_threshold = max(zero_far, key=lambda row: row["recognition_accuracy"]) if zero_far else max(threshold_rows, key=lambda row: row["balanced_accuracy"])
    metrics = {
        "dataset": "LFW via Figshare mirror (CC BY 4.0 metadata)",
        "warning": "Engineering stress test only; not a real classroom accuracy or demographic-performance claim.",
        "model": "buffalo_s / ArcFace / CPUExecutionProvider",
        "registered_identities": len(registered),
        "unknown_impostor_identities": len(unknown),
        "present_roster_students": 500,
        "absent_roster_students": 500,
        "registered_profile_vectors": int(db.index.ntotal),
        "embedding_dimension": db.dimension,
        "raw_vector_storage_mb": db.index.ntotal * db.dimension * 4 / (1024 * 1024),
        "mean_enrollment_samples": float(np.mean(enrollment_counts)) if enrollment_counts else 0.0,
        "enrollment_failures": enrollment_failures,
        "rss_before_mb": baseline_rss,
        "rss_after_index_mb": rss_mb(),
        "threshold_selected_for_zero_far": selected_threshold,
        "threshold_sweep": threshold_rows,
        "average_inference_latency_ms": float(np.mean(latency_ms)) if latency_ms else 0.0,
        "p95_inference_latency_ms": float(np.percentile(latency_ms, 95)) if latency_ms else 0.0,
        "detected_capture_count": sum(row["detected"] for row in scores),
        "capture_count": len(scores),
    }
    serializer = lambda value: value.item() if hasattr(value, "item") else str(value)
    (OUT / "benchmark_report.json").write_text(json.dumps(metrics, indent=2, default=serializer))
    (OUT / "score_rows.json").write_text(json.dumps(scores, indent=2, default=serializer))
    print(json.dumps(metrics, indent=2, default=serializer))
    del engine, db
    gc.collect()


if __name__ == "__main__":
    main()
