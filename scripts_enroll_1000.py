import os
import cv2
from pathlib import Path
from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from core.quality import FaceQualityChecker
from learning.profile_manager import ProfileManager
from db.profiles import ProfileStore
from db.database import LocalDatabase

def main():
    print("Initializing components...")
    detector = FaceDetector()
    embedder = FaceEmbedder()
    quality = FaceQualityChecker()
    
    # Clean old DBs
    for f in ["faiss_1000.bin", "meta_1000.json", "profiles_1000.db"]:
        if os.path.exists(f): os.remove(f)
        
    vector_db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    profile_store = ProfileStore("profiles_1000.db")
    manager = ProfileManager(profile_store, vector_db)
    
    enroll_dir = Path("dataset_1000/enrollment")
    identities = [d for d in enroll_dir.iterdir() if d.is_dir()]
    
    print(f"Enrolling {len(identities)} identities...")
    success = 0
    
    for i, identity in enumerate(identities):
        images = list(identity.glob("*.jpg"))
        if not images: continue
        
        img = cv2.imread(str(images[0]))
        faces = detector.detect(img)
        if len(faces) != 1:
            print(f"Skipping {identity.name}: found {len(faces)} faces.")
            continue
            
        res = quality.check(img, faces[0])
        if not res.accepted:
            print(f"Skipping {identity.name}: {res.reason}")
            continue
            
        emb = embedder.generate_embedding(img, faces[0])
        if emb is None: continue
        
        manager.create_initial_profile(identity.name, "CLASS_1000", [emb])
        success += 1
        
        if (i+1) % 50 == 0:
            print(f"Processed {i+1}/{len(identities)}...")
            
    print(f"Successfully enrolled {success} identities.")

if __name__ == "__main__":
    main()
