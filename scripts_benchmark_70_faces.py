import cv2
import json
import time
from pathlib import Path
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase

def main():
    print("=== 70-FACE THROUGHPUT BENCHMARK ===")
    db = LocalDatabase("faiss_1000.bin", "meta_1000.json")
    engine = AttendanceEngine(db, similarity_threshold=0.45, review_threshold=0.35, min_observations=1)
    
    img_path = Path("dataset_1000/classrooms/scenario_70_faces.jpg")
    if not img_path.exists():
        print("70-face classroom image not found. Run scripts_generate_classroom.py first.")
        return
        
    img = cv2.imread(str(img_path))
    
    # Warmup
    print("Warming up...")
    engine.process_frame(img, classroom_id="CLASS_1000")
    
    print("Measuring inference latency...")
    runs = 5
    total_time = 0
    for i in range(runs):
        start = time.perf_counter()
        results = engine.process_frame(img, classroom_id="CLASS_1000")
        elapsed = time.perf_counter() - start
        total_time += elapsed
        print(f"  Run {i+1}: {elapsed:.2f}s ({len(results)} faces)")
        
    avg_time = total_time / runs
    fps = 1.0 / avg_time
    
    print(f"\nAverage time per 70-face frame: {avg_time:.2f} seconds")
    print(f"Estimated FPS: {fps:.2f}")
    
    if hasattr(engine, 'batch_embedder'):
        print(f"Execution Provider: {engine.batch_embedder.provider}")
        if engine.batch_embedder.provider == "CPUExecutionProvider":
            print("\nWARNING: Running on CPU. 70-face processing requires GPU acceleration (CUDA/TensorRT) for real-time framerates.")
            
if __name__ == "__main__":
    main()
