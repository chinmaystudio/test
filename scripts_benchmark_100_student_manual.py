"""End-to-end 100-student manual-capture benchmark for NeuroClass.

This uses a public LFW mirror only as a reproducible engineering stress test. It is
not a claim about real classroom accuracy or demographic performance. One hundred
identities are enrolled; 50 are treated as present, 50 as absent, and 50 additional
identities are used as unknown impostors. The actual AttendanceEngine, ArcFace
embedding path, classroom filter, temporal policy, and manual capture mode are used.
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from uuid import UUID, uuid5

import cv2
import numpy as np

from core.attendance_engine import AttendanceEngine
from core.batch_embedder import BatchFaceEmbedder
from db.database import LocalDatabase

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "validation_data" / "lfw"
OUT = ROOT / "validation_data" / "benchmark_100"
CLASSROOM_ID = "benchmark-classroom-100"
NAMESPACE = UUID("1f1a1fc8-4e4c-4cc2-a367-6a7e56e2f02a")


def image_files(identity: Path) -> list[Path]:
    return sorted(identity.glob("*.jpg"))


def choose_identities() -> list[tuple[str, list[Path]]]:
    candidates = [(path.name, image_files(path)) for path in DATASET.iterdir() if path.is_dir()]
    candidates = [(name, files) for name, files in candidates if len(files) >= 3]
    candidates.sort(key=lambda row: row[0])
    random.Random(42).shuffle(candidates)
    return candidates[:150]


def aligned_embedding(engine: AttendanceEngine, image: np.ndarray):
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
        crop = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)
    return engine.batch_embedder.generate_embeddings_batch([crop], batch_size=1)[0]


def make_composite(present: list[tuple[str, Path]], output: Path) -> None:
    cell = 180
    columns = 10
    rows = int(np.ceil(len(present) / columns))
    canvas = np.zeros((rows * cell, columns * cell, 3), dtype=np.uint8)
    for index, (_, image_path) in enumerate(present):
        image = cv2.imread(str(image_path))
        image = cv2.resize(image, (cell - 20, cell - 20), interpolation=cv2.INTER_CUBIC)
        row, column = divmod(index, columns)
        y, x = row * cell + 10, column * cell + 10
        canvas[y:y + cell - 20, x:x + cell - 20] = image
    cv2.imwrite(str(output), canvas)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    selected = choose_identities()
    if len(selected) < 150:
        raise RuntimeError(f"Need 150 identities with at least two images; found {len(selected)}")

    enrolled = selected[:100]
    unknown = selected[100:150]
    present = [(identity, files[2]) for identity, files in enrolled[:50]]
    absent = [(identity, files[2]) for identity, files in enrolled[50:]]
    unknown = [(identity, files[2]) for identity, files in unknown]
    db = LocalDatabase(str(OUT / "faiss.index"), str(OUT / "metadata.json"))
    engine = AttendanceEngine(db, similarity_threshold=0.55, review_threshold=0.45, min_observations=5)
    engine.batch_embedder = BatchFaceEmbedder()
    classroom = CLASSROOM_ID

    enrollment_failures = []
    for identity, files in enrolled:
        student_id = str(uuid5(NAMESPACE, identity))
        embeddings_added = 0
        for enrollment_path in files[:2]:
            image = cv2.imread(str(enrollment_path))
            embedding = aligned_embedding(engine, image)
            if embedding is None:
                continue
            db.add_embedding(embedding, {"student_id": student_id, "classroom_id": classroom, "name": identity})
            embeddings_added += 1
        if embeddings_added == 0:
            enrollment_failures.append(identity)

    def evaluate(rows: list[tuple[str, Path]], should_match: bool):
        outcomes = []
        for identity, image_path in rows:
            expected_id = str(uuid5(NAMESPACE, identity)) if should_match else None
            image = cv2.imread(str(image_path))
            started = time.perf_counter()
            results = engine.process_frame(image, classroom, lecture_id="manual-benchmark", capture_mode="manual")
            latency_ms = (time.perf_counter() - started) * 1000
            best = next((result for result in results if result.get("status") == "PRESENT"), None)
            predicted_id = best.get("student_id") if best else None
            outcomes.append({
                "identity": identity,
                "expected_student_id": expected_id,
                "predicted_student_id": predicted_id,
                "status": best.get("status") if best else "UNKNOWN",
                "similarity": best.get("similarity") if best else None,
                "latency_ms": latency_ms,
                "correct": predicted_id == expected_id if should_match else predicted_id is None,
            })
        return outcomes

    genuine = evaluate(present, True)
    impostor = evaluate(unknown, False)
    composite_path = OUT / "composite_50_present_faces.jpg"
    make_composite(present, composite_path)
    composite_image = cv2.imread(str(composite_path))
    composite_started = time.perf_counter()
    composite_results = engine.process_frame(composite_image, classroom, lecture_id="manual-composite", capture_mode="manual")
    composite_latency_ms = (time.perf_counter() - composite_started) * 1000

    tp = sum(row["correct"] for row in genuine)
    fn = len(genuine) - tp
    fp = sum(not row["correct"] for row in impostor)
    tn = len(impostor) - fp
    report = {
        "dataset": "LFW via Figshare mirror (CC BY 4.0 metadata)",
        "warning": "This is an engineering stress test on public celebrity images, not a real classroom accuracy guarantee.",
        "model_path": "buffalo_s / ArcFace server-side AttendanceEngine",
        "enrolled_students": len(enrolled),
        "present_roster_students": len(present),
        "absent_roster_students": len(absent),
        "unknown_impostors": len(unknown),
        "enrollment_failures": enrollment_failures,
        "genuine_true_positive": tp,
        "genuine_false_negative": fn,
        "impostor_false_positive": fp,
        "impostor_true_negative": tn,
        "genuine_recognition_accuracy": tp / len(genuine) if genuine else 0.0,
        "false_rejection_rate": fn / len(genuine) if genuine else 0.0,
        "false_acceptance_rate": fp / len(impostor) if impostor else 0.0,
        "average_genuine_latency_ms": float(np.mean([row["latency_ms"] for row in genuine])) if genuine else 0.0,
        "p95_genuine_latency_ms": float(np.percentile([row["latency_ms"] for row in genuine], 95)) if genuine else 0.0,
        "composite_faces_submitted": len(present),
        "composite_faces_detected_and_returned": len(composite_results),
        "composite_latency_ms": composite_latency_ms,
        "genuine_rows": genuine,
        "impostor_rows": impostor,
        "composite_image": str(composite_path),
    }
    (OUT / "benchmark_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({key: value for key, value in report.items() if key not in {"genuine_rows", "impostor_rows"}}, indent=2))


if __name__ == "__main__":
    main()
