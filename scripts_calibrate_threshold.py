import cv2
import numpy as np
import json
from pathlib import Path
from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from db.database import LocalDatabase

def main():
    print("Loading components for calibration...")
    detector = FaceDetector()
    embedder = FaceEmbedder()
    db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    
    val_dir = Path("dataset_1000/validation")
    unk_dir = Path("dataset_1000/unknown")
    
    reg_pool = [d for d in val_dir.iterdir() if d.is_dir()]
    unk_pool = [d for d in unk_dir.iterdir() if d.is_dir()]
    
    scores = []
    
    print("Processing validation registered faces...")
    for p in reg_pool:
        imgs = list(p.glob("*.jpg"))
        if not imgs: continue
        img = cv2.imread(str(imgs[0]))
        faces = detector.detect(img)
        if len(faces) != 1: continue
        emb = embedder.generate_embedding(img, faces[0])
        if emb is None: continue
        
        matches = db.search(emb, k=2)
        if not matches: continue
        
        scores.append({
            "gt": p.name,
            "pred": matches[0]["student_id"],
            "sim": matches[0]["similarity"],
            "margin": matches[0]["similarity"] - (matches[1]["similarity"] if len(matches) > 1 else 0),
            "type": "REGISTERED"
        })
        
    print("Processing validation unknown faces...")
    for p in unk_pool:
        imgs = list(p.glob("*.jpg"))
        if not imgs: continue
        img = cv2.imread(str(imgs[0]))
        faces = detector.detect(img)
        if len(faces) != 1: continue
        emb = embedder.generate_embedding(img, faces[0])
        if emb is None: continue
        
        matches = db.search(emb, k=1)
        if not matches: continue
        
        scores.append({
            "gt": p.name,
            "pred": matches[0]["student_id"],
            "sim": matches[0]["similarity"],
            "type": "UNKNOWN"
        })
        
    print("\n--- THRESHOLD CALIBRATION ---")
    for thresh in np.arange(0.30, 0.75, 0.05):
        fa = sum(1 for s in scores if s["type"] == "UNKNOWN" and s["sim"] >= thresh)
        fr = sum(1 for s in scores if s["type"] == "REGISTERED" and s["sim"] < thresh)
        ta = sum(1 for s in scores if s["type"] == "REGISTERED" and s["sim"] >= thresh and s["pred"] == s["gt"])
        swaps = sum(1 for s in scores if s["type"] == "REGISTERED" and s["sim"] >= thresh and s["pred"] != s["gt"])
        
        print(f"Threshold {thresh:.2f}: FAR={fa} FRR={fr} Swaps={swaps} TA={ta}")
        
    print("Calibration complete.")

if __name__ == "__main__":
    main()
