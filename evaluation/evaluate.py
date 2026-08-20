"""Evaluate enrolled embeddings on a held-out folder.

Expected layout:
  dataset/validation/<student_id>/*.jpg
  dataset/validation/unknown/*.jpg

Use different images from enrollment to avoid leakage.
"""
import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from db.database import LocalDatabase


def collect_scores(root: Path, database: LocalDatabase):
    detector, embedder = FaceDetector(), FaceEmbedder()
    scores = []
    for identity_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        expected = None if identity_dir.name.lower() == "unknown" else identity_dir.name
        for path in sorted(identity_dir.glob("*")):
            image = cv2.imread(str(path))
            if image is None:
                continue
            start = time.perf_counter()
            faces = detector.detect(image)
            elapsed = time.perf_counter() - start
            if len(faces) != 1:
                scores.append({"expected": expected, "predicted": None, "similarity": 0.0, "time": elapsed})
                continue
            embedding = embedder.generate_embedding(image, faces[0])
            matches = database.search(embedding, k=1) if embedding is not None else []
            match = matches[0] if matches else None
            scores.append({"expected": expected, "predicted": match["student_id"] if match else None,
                           "similarity": float(match["similarity"]) if match else 0.0, "time": elapsed})
    return scores


def metrics(scores, threshold: float):
    tp = fp = tn = fn = 0
    for row in scores:
        accepted = row["predicted"] is not None and row["similarity"] >= threshold
        genuine = row["expected"] is not None
        correct = accepted and row["predicted"] == row["expected"]
        if genuine and correct: tp += 1
        elif genuine and not accepted: fn += 1
        elif not genuine and accepted: fp += 1
        else: tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"threshold": threshold, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "false_acceptance_rate": fp / (fp + tn) if fp + tn else 0.0,
            "false_rejection_rate": fn / (fn + tp) if fn + tp else 0.0,
            "precision": precision, "recall": recall, "f1": f1}


def evaluate(root: str, index: str, metadata: str):
    database = LocalDatabase(index, metadata)
    scores = collect_scores(Path(root), database)
    rows = [metrics(scores, threshold / 100) for threshold in range(35, 91, 5)]
    best = min(rows, key=lambda row: (row["false_acceptance_rate"], -row["f1"])) if rows else None
    print({"samples": len(scores), "average_seconds": np.mean([r["time"] for r in scores]) if scores else 0.0,
           "thresholds": rows, "recommended": best})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="dataset/validation")
    parser.add_argument("--index", default="faiss_index.bin")
    parser.add_argument("--metadata", default="metadata.json")
    args = parser.parse_args()
    evaluate(args.data, args.index, args.metadata)
