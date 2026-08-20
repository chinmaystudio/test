import cv2
import numpy as np
import random
import json
from pathlib import Path

def generate_classroom(registered_pool, unknown_pool, num_registered, num_unknown, output_path, meta_path):
    reg_selected = random.sample(registered_pool, min(num_registered, len(registered_pool)))
    unk_selected = random.sample(unknown_pool, min(num_unknown, len(unknown_pool)))
    
    all_faces = []
    for p in reg_selected:
        imgs = list(p.glob("*.jpg"))
        if imgs: all_faces.append((imgs[0], p.name, "REGISTERED"))
        
    for p in unk_selected:
        imgs = list(p.glob("*.jpg"))
        if imgs: all_faces.append((imgs[0], p.name, "UNKNOWN"))
        
    random.shuffle(all_faces)
    
    total = len(all_faces)
    if total == 0: return
    
    cols = int(np.ceil(np.sqrt(total)))
    rows = int(np.ceil(total / cols))
    
    face_w, face_h = 100, 100
    composite = np.zeros((rows * face_h, cols * face_w, 3), dtype=np.uint8)
    
    metadata = {
        "image_id": output_path.stem,
        "registered_students_present": len(reg_selected),
        "unknown_students_present": len(unk_selected),
        "faces": []
    }
    
    for idx, (img_path, name, type_) in enumerate(all_faces):
        img = cv2.imread(str(img_path))
        if img is None: continue
        img = cv2.resize(img, (face_w, face_h))
        
        r, c = divmod(idx, cols)
        y1, y2 = r * face_h, (r + 1) * face_h
        x1, x2 = c * face_w, (c + 1) * face_w
        
        composite[y1:y2, x1:x2] = img
        metadata["faces"].append({
            "bbox": [x1, y1, x2, y2],
            "ground_truth_identity": name,
            "ground_truth_type": type_
        })
        
    cv2.imwrite(str(output_path), composite)
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    test_dir = Path("dataset_1000/test")
    unknown_dir = Path("dataset_1000/unknown")
    out_dir = Path("dataset_1000/classrooms")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    reg_pool = [d for d in test_dir.iterdir() if d.is_dir()]
    unk_pool = [d for d in unknown_dir.iterdir() if d.is_dir()]
    
    scenarios = [
        (30, 5, "scenario_A"),
        (50, 10, "scenario_B"),
        (70, 0, "scenario_70_faces"),
        (100, 20, "scenario_C")
    ]
    
    random.seed(42)
    for n_reg, n_unk, name in scenarios:
        print(f"Generating {name}...")
        generate_classroom(reg_pool, unk_pool, n_reg, n_unk, out_dir / f"{name}.jpg", out_dir / f"{name}.json")
        
    print("Classroom generation complete.")

if __name__ == "__main__":
    main()
