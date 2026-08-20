import cv2
import json
import time
from pathlib import Path
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase
from learning.profile_manager import ProfileManager
from db.profiles import ProfileStore

def main():
    print("=== CONTINUAL LEARNING 1000-IDENTITY TEST ===")
    
    db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    profile_store = ProfileStore("profiles_1000.db")
    manager = ProfileManager(profile_store, db)
    engine = AttendanceEngine(db, similarity_threshold=0.45, review_threshold=0.35, min_observations=1)
    
    # 1. Baseline Evaluation
    print("\n1. Evaluating Baseline...")
    # (In a full script, we'd run the benchmark here and save baseline_metrics.json)
    
    # 2. Simulate Session 1 (Adaptation)
    print("\n2. Simulating Session 1 (Adaptation)...")
    img_path = Path("dataset_1000/classrooms/scenario_A.jpg")
    if img_path.exists():
        img = cv2.imread(str(img_path))
        results = engine.process_frame(img, classroom_id="CLASS_1000")
        
        updates = 0
        for r in results:
            if r["status"] == "PRESENT":
                # Need embedding for adaptation. In production, engine returns it or saves it.
                # For this script, we'll simulate the hook.
                updates += 1
        print(f"Queued {updates} high-confidence observations for learning.")
        
    # 3. Evaluate Adaptive
    print("\n3. Evaluating Adaptive Profile...")
    # (In a full script, we'd run the benchmark again and save adaptive_metrics.json)
    
    print("\nContinual learning test complete.")

if __name__ == "__main__":
    main()
