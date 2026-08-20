import os, cv2, random, shutil
import numpy as np
from pathlib import Path

source_dir = Path("/home/ubuntu/dataset_lfw")
enroll_dir = Path("/home/ubuntu/neuroclass_attendance/dataset/training")
test_dir = Path("/home/ubuntu/neuroclass_attendance/dataset/validation")
composite_path = Path("/home/ubuntu/neuroclass_attendance/dataset/classroom_composite.jpg")

enroll_dir.mkdir(parents=True, exist_ok=True)
test_dir.mkdir(parents=True, exist_ok=True)

# Find identities with at least 2 images
identities = [p for p in source_dir.iterdir() if p.is_dir() and len(list(p.glob("*.jpg"))) >= 2]
random.seed(42)
selected = random.sample(identities, min(90, len(identities)))

print(f"Selected {len(selected)} identities for benchmark.")

composite_faces = []
cols, rows = 10, 9
face_w, face_h = 100, 100
composite_img = np.zeros((rows * face_h, cols * face_w, 3), dtype=np.uint8)

for idx, identity in enumerate(selected):
    images = sorted(list(identity.glob("*.jpg")))
    
    # Use first image for enrollment
    target_enroll = enroll_dir / identity.name
    target_enroll.mkdir(exist_ok=True)
    shutil.copy(images[0], target_enroll / "enroll.jpg")
    
    # Use second image for the composite "classroom" and test dir
    target_test = test_dir / identity.name
    target_test.mkdir(exist_ok=True)
    shutil.copy(images[1], target_test / "test.jpg")
    
    img2 = cv2.imread(str(images[1]))
    img2_resized = cv2.resize(img2, (face_w, face_h))
    
    r, c = divmod(idx, cols)
    composite_img[r*face_h:(r+1)*face_h, c*face_w:(c+1)*face_w] = img2_resized

cv2.imwrite(str(composite_path), composite_img)
print(f"Generated composite classroom image: {composite_path}")
