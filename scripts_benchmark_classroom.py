import time, cv2
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase

db = LocalDatabase("faiss_index.bin", "metadata.json")
engine = AttendanceEngine(db, similarity_threshold=0.40, review_threshold=0.30, min_observations=1)

img = cv2.imread("dataset/classroom_composite.jpg")
# Scale down to speed up CPU inference
img = cv2.resize(img, (640, 640))
start = time.perf_counter()
results = engine.process_frame(img, classroom_id="CLASS-90", lecture_id="L1")
elapsed = time.perf_counter() - start

print(f"\n--- BENCHMARK RESULTS ---")
print(f"Total time: {elapsed:.2f} seconds")
print(f"Faces detected: {len(results)}")
print(f"Recognized (PRESENT): {len([r for r in results if r['status'] == 'PRESENT'])}")
print(f"Uncertain (REVIEW): {len([r for r in results if r['status'] == 'REVIEW'])}")
print(f"Unknown: {len([r for r in results if r['status'] == 'UNKNOWN'])}")
