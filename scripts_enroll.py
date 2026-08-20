"""Enroll one student from a directory of images.

Usage:
  python scripts_enroll.py --student-id STU024 --name Aarav --roll-number 24 --classroom-id CSE-A --images dataset/training/STU024
"""
import argparse
from pathlib import Path

import cv2

from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from db.database import LocalDatabase
from core.quality import FaceQualityChecker


def enroll(args) -> int:
    detector, embedder, quality, database = FaceDetector(), FaceEmbedder(), FaceQualityChecker(), LocalDatabase(args.index, args.metadata)
    added = 0
    for path in sorted(Path(args.images).glob("*")):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        image = cv2.imread(str(path))
        if image is None:
            print(f"SKIP {path}: unreadable")
            continue
        faces = detector.detect(image)
        if len(faces) != 1:
            print(f"SKIP {path}: expected exactly one face, found {len(faces)}")
            continue
        result = quality.check(image, faces[0])
        if not result.accepted:
            print(f"SKIP {path}: {result.reason}")
            continue
        embedding = embedder.generate_embedding(image, faces[0])
        if embedding is None:
            print(f"SKIP {path}: embedding unavailable")
            continue
        database.add_embedding(embedding, {"student_id": args.student_id, "name": args.name,
                                           "roll_number": args.roll_number, "classroom_id": args.classroom_id,
                                           "quality_score": result.score})
        added += 1
    print(f"Added {added} embeddings for {args.student_id}")
    return added


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--roll-number", required=True)
    parser.add_argument("--classroom-id", required=True)
    parser.add_argument("--images", required=True)
    parser.add_argument("--index", default="faiss_index.bin")
    parser.add_argument("--metadata", default="metadata.json")
    enroll(parser.parse_args())
