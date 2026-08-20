import os
import shutil
import random
from pathlib import Path
from sklearn.datasets import fetch_lfw_people
import cv2

def main():
    print("Downloading/loading LFW dataset (requires at least 3 images per identity)...")
    # We need at least 3 images: 1 for enrollment, 1 for validation, 1 for test
    lfw = fetch_lfw_people(min_faces_per_person=3, resize=1.0, color=True)
    print(f"Loaded {len(lfw.images)} images across {len(lfw.target_names)} identities.")
    
    # We need 1000 identities for registered, and some for unknowns.
    # LFW with min_faces=3 has around 400-500 identities.
    # If we can't reach 1000, we'll use what's available and warn the user.
    available_ids = list(range(len(lfw.target_names)))
    random.seed(42)
    random.shuffle(available_ids)
    
    target_registered = 1000
    if len(available_ids) < target_registered + 50:
        print(f"WARNING: LFW only has {len(available_ids)} identities with >=3 images.")
        print(f"Using {len(available_ids)-50} for registered and 50 for unknowns.")
        registered_ids = available_ids[:-50]
        unknown_ids = available_ids[-50:]
    else:
        registered_ids = available_ids[:target_registered]
        unknown_ids = available_ids[target_registered:target_registered+50]
        
    base_dir = Path("dataset_1000")
    enroll_dir = base_dir / "enrollment"
    val_dir = base_dir / "validation"
    test_dir = base_dir / "test"
    unknown_dir = base_dir / "unknown"
    
    for d in [enroll_dir, val_dir, test_dir, unknown_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    print("Distributing registered identities...")
    for target in registered_ids:
        name = lfw.target_names[target].replace(" ", "_")
        indices = [i for i, t in enumerate(lfw.target) if t == target]
        
        # Split: 1 enroll, 1 val, rest test
        enroll_idx = indices[0]
        val_idx = indices[1]
        test_indices = indices[2:]
        
        # Save enroll
        edir = enroll_dir / name
        edir.mkdir(exist_ok=True)
        img = cv2.cvtColor((lfw.images[enroll_idx] * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(edir / "enroll_01.jpg"), img)
        
        # Save val
        vdir = val_dir / name
        vdir.mkdir(exist_ok=True)
        img = cv2.cvtColor((lfw.images[val_idx] * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(vdir / "val_01.jpg"), img)
        
        # Save test
        tdir = test_dir / name
        tdir.mkdir(exist_ok=True)
        for i, idx in enumerate(test_indices):
            img = cv2.cvtColor((lfw.images[idx] * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(tdir / f"test_{i:02d}.jpg"), img)
            
    print("Distributing unknown identities...")
    for target in unknown_ids:
        name = lfw.target_names[target].replace(" ", "_")
        indices = [i for i, t in enumerate(lfw.target) if t == target]
        udir = unknown_dir / name
        udir.mkdir(exist_ok=True)
        for i, idx in enumerate(indices):
            img = cv2.cvtColor((lfw.images[idx] * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(udir / f"unknown_{i:02d}.jpg"), img)
            
    print("Dataset preparation complete.")

if __name__ == "__main__":
    main()
