import cv2
import json
import time
from pathlib import Path
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase
from db.profiles import ProfileStore

def main():
    print("Loading 1000-identity database...")
    db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    profile_store = ProfileStore("profiles_1000.db")
    engine = AttendanceEngine(db, similarity_threshold=0.45, review_threshold=0.35, min_observations=1)
    
    classrooms = Path("dataset_1000/classrooms").glob("*.jpg")
    
    total_faces = 0
    total_fa = 0
    total_fr = 0
    total_swaps = 0
    total_ta = 0
    total_tr = 0
    
    for img_path in classrooms:
        meta_path = img_path.with_suffix(".json")
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            
        img = cv2.imread(str(img_path))
        print(f"\nProcessing {img_path.name} ({meta['registered_students_present']} reg, {meta['unknown_students_present']} unk)...")
        
        start = time.perf_counter()
        results = engine.process_frame(img, classroom_id="CLASS_1000")
        elapsed = time.perf_counter() - start
        
        print(f"Detected {len(results)} faces in {elapsed:.2f}s")
        
        # Simple evaluation (assuming detector finds them in roughly same order/location)
        # For a rigorous benchmark, we'd do IoU matching between prediction bboxes and ground truth bboxes.
        # For this prototype, we'll just check the sets of predicted IDs vs ground truth IDs.
        
        gt_reg = set(f["ground_truth_identity"] for f in meta["faces"] if f["ground_truth_type"] == "REGISTERED")
        gt_unk = sum(1 for f in meta["faces"] if f["ground_truth_type"] == "UNKNOWN")
        
        pred_reg = set(r["student_id"] for r in results if r["status"] == "PRESENT")
        pred_unk = sum(1 for r in results if r["status"] == "UNKNOWN" or r["status"] == "REVIEW")
        
        ta = len(gt_reg.intersection(pred_reg))
        fr = len(gt_reg - pred_reg)
        fa = len(pred_reg - gt_reg) # Could be unknowns or swaps
        
        print(f"  True Accepts: {ta}")
        print(f"  False Rejects: {fr}")
        print(f"  False Accepts/Swaps: {fa}")
        
        total_faces += len(meta["faces"])
        total_ta += ta
        total_fr += fr
        total_fa += fa
        
    print("\n=== FINAL BENCHMARK RESULTS ===")
    print(f"Total Test Faces: {total_faces}")
    print(f"True Accepts: {total_ta}")
    print(f"False Rejects: {total_fr}")
    print(f"False Accepts: {total_fa}")
    
    if total_fa == 0 and total_fr == 0:
        print("100% benchmark accuracy on the defined test set.")
    else:
        print(f"Accuracy: {total_ta / total_faces * 100:.2f}%")
        
if __name__ == "__main__":
    main()
