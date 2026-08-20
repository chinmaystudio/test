"""Compare buffalo_s and buffalo_l on NeuroClass validation data.

The preferred dataset is the existing classroom validation set:
  dataset_1000/enrollment/<identity>/enroll_01.jpg
  dataset_1000/classrooms/scenario_*.jpg + scenario_*.json

Each classroom annotation supplies a ground-truth identity/type and bounding
box. The script loads one model, evaluates it, releases it, then loads the
other model, so the models are never resident simultaneously.
"""
import argparse
import gc
import json
import time
from pathlib import Path

import cv2
import numpy as np
import psutil
from insightface.app import FaceAnalysis


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


def normalize(embedding):
    vector = np.asarray(embedding, dtype=np.float32)
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def prepare_image(image):
    if image is None:
        return None
    max_dimension = max(image.shape[:2])
    if max_dimension < 640:
        scale = 640 / max_dimension
        image = cv2.resize(image, (int(image.shape[1] * scale), int(image.shape[0] * scale)), interpolation=cv2.INTER_CUBIC)
    return image


def embed_image(app, image):
    image = prepare_image(image)
    if image is None:
        return None, 0.0
    started = time.perf_counter()
    faces = app.get(image)
    elapsed = time.perf_counter() - started
    if len(faces) == 1 and hasattr(faces[0], "embedding"):
        return normalize(faces[0].embedding), elapsed
    # The bundled LFW-style crops are already face-aligned. Use the recognition
    # model directly as a benchmark fallback when detection rejects the tiny crop.
    aligned = cv2.resize(image, (112, 112), interpolation=cv2.INTER_AREA)
    embedding = app.models["recognition"].get_feat([aligned])
    if embedding is None or len(embedding) == 0:
        return None, elapsed
    return normalize(embedding[0]), elapsed


def load_prototypes(app, enrollment_root: Path, identities):
    prototypes = {}
    for identity in sorted(identities):
        candidates = sorted((enrollment_root / identity).glob("*.jpg"))
        if not candidates:
            continue
        image = cv2.imread(str(candidates[0]))
        embedding, _ = embed_image(app, image)
        if embedding is not None:
            prototypes[identity] = embedding
    return prototypes


def evaluate_model(model_name: str, enrollment_root: Path, classroom_root: Path, threshold: float):
    before = rss_mb()
    load_started = time.perf_counter()
    app = FaceAnalysis(
        name=model_name,
        allowed_modules=["detection", "recognition"],
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(640, 640))
    load_seconds = time.perf_counter() - load_started
    after_load = rss_mb()

    scenarios = []
    identities = set()
    for annotation_path in sorted(classroom_root.glob("scenario_*.json")):
        annotation = json.loads(annotation_path.read_text())
        scenarios.append((classroom_root / f"{annotation['image_id']}.jpg", annotation))
        identities.update(
            face["ground_truth_identity"]
            for face in annotation.get("faces", [])
            if face.get("ground_truth_type") == "REGISTERED"
        )
    prototypes = load_prototypes(app, enrollment_root, identities)

    rows = []
    for image_path, annotation in scenarios:
        image = cv2.imread(str(image_path))
        for face in annotation.get("faces", []):
            x1, y1, x2, y2 = [int(value) for value in face["bbox"]]
            crop = image[max(0, y1):max(y1 + 1, y2), max(0, x1):max(x1 + 1, x2)]
            embedding, latency = embed_image(app, crop)
            best_identity = None
            best_similarity = 0.0
            if embedding is not None and prototypes:
                scored = [(identity, float(np.dot(embedding, prototype))) for identity, prototype in prototypes.items()]
                best_identity, best_similarity = max(scored, key=lambda item: item[1])
            accepted = best_identity is not None and best_similarity >= threshold
            expected = face.get("ground_truth_identity") if face.get("ground_truth_type") == "REGISTERED" else None
            rows.append({
                "expected": expected,
                "predicted": best_identity if accepted else None,
                "similarity": best_similarity,
                "latency_seconds": latency,
                "genuine": expected is not None,
            })

    tp = sum(row["genuine"] and row["predicted"] == row["expected"] for row in rows)
    fn = sum(row["genuine"] and row["predicted"] != row["expected"] for row in rows)
    fp = sum((not row["genuine"]) and row["predicted"] is not None for row in rows)
    tn = sum((not row["genuine"]) and row["predicted"] is None for row in rows)
    genuine_total = tp + fn
    unknown_total = fp + tn
    latencies = [row["latency_seconds"] for row in rows]
    metrics = {
        "model": model_name,
        "scenarios": len(scenarios),
        "faces_evaluated": len(rows),
        "enrolled_identities": len(prototypes),
        "threshold": threshold,
        "recognition_accuracy": tp / genuine_total if genuine_total else 0.0,
        "false_acceptance_rate": fp / unknown_total if unknown_total else 0.0,
        "false_rejection_rate": fn / genuine_total if genuine_total else 0.0,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "average_inference_latency_ms": (np.mean(latencies) * 1000) if latencies else 0.0,
        "p95_inference_latency_ms": (np.percentile(latencies, 95) * 1000) if latencies else 0.0,
        "model_load_seconds": load_seconds,
        "memory_before_model_mb": before,
        "memory_after_model_mb": after_load,
        "model_memory_increase_mb": after_load - before,
    }
    del app
    gc.collect()
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--enrollment", default="dataset_1000/enrollment")
    parser.add_argument("--classrooms", default="dataset_1000/classrooms")
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--output", default="benchmark_models.json")
    args = parser.parse_args()

    results = []
    for model_name in ("buffalo_s", "buffalo_l"):
        try:
            results.append(evaluate_model(model_name, Path(args.enrollment), Path(args.classrooms), args.threshold))
        except Exception as exc:
            results.append({"model": model_name, "error": str(exc)})

    Path(args.output).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
