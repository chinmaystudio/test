import os
import shutil
import numpy as np
from pathlib import Path

from db.database import LocalDatabase
from db.profiles import ProfileStore
from learning.profile_manager import ProfileManager


def generate_dummy_embedding(base, noise_level=0.05):
    noise = np.random.normal(0, noise_level, len(base))
    emb = np.array(base) + noise
    norm = np.linalg.norm(emb)
    return (emb / norm).tolist()


def main():
    print("=== NeuroClass Continual Learning Demonstration ===")
    
    # Cleanup old DBs
    for f in ["profiles.db", "demo_faiss.bin", "demo_meta.json"]:
        if os.path.exists(f): os.remove(f)
        
    vector_db = LocalDatabase("demo_faiss.bin", "demo_meta.json")
    profile_store = ProfileStore("profiles.db")
    manager = ProfileManager(profile_store, vector_db)
    
    student_id = "STU_001"
    classroom_id = "CLASS_A"
    
    print("\n1. STUDENT REGISTRATION")
    # Base ideal embedding
    base_emb = np.random.randn(512)
    base_emb = (base_emb / np.linalg.norm(base_emb)).tolist()
    
    enroll_embs = [generate_dummy_embedding(base_emb, 0.02) for _ in range(5)]
    print(f"Captured {len(enroll_embs)} face samples.")
    
    profile = manager.create_initial_profile(student_id, classroom_id, enroll_embs)
    print(f"Created Initial Identity Profile Version {profile.profile_version}")
    
    print("\n2. ATTENDANCE SESSION 1 (High Confidence)")
    # Simulate a good observation
    obs1 = generate_dummy_embedding(base_emb, 0.04) # Slightly different
    res1 = manager.queue_observation(student_id, obs1, confidence="HIGH", margin=0.20)
    print(f"Observation 1 result: {res1['status']} - {res1['reason']}")
    
    print("\n3. ATTENDANCE SESSION 2 (Redundant)")
    # Simulate an observation too similar to existing
    obs2 = enroll_embs[0] # Exact copy
    res2 = manager.queue_observation(student_id, obs2, confidence="HIGH", margin=0.20)
    print(f"Observation 2 result: {res2['status']} - {res2['reason']}")
    
    print("\n4. ATTENDANCE SESSION 3 (Ambiguous Match)")
    # Simulate an observation where margin is too low (e.g. looks like twins)
    obs3 = generate_dummy_embedding(base_emb, 0.05)
    res3 = manager.queue_observation(student_id, obs3, confidence="HIGH", margin=0.05)
    print(f"Observation 3 result: {res3['status']} - {res3['reason']}")
    
    print("\n5. ATTENDANCE SESSION 4 (Outlier / Spoof attempt)")
    # Simulate a completely different embedding matching the ID
    obs4 = np.random.randn(512)
    obs4 = (obs4 / np.linalg.norm(obs4)).tolist()
    res4 = manager.queue_observation(student_id, obs4, confidence="HIGH", margin=0.20)
    print(f"Observation 4 result: {res4['status']} - {res4['reason']}")
    
    print("\n6. REVIEWING PROFILE")
    final_profile = profile_store.get_profile(student_id)
    print(f"Final Profile Version: {final_profile.profile_version}")
    print(f"Enrollment embeddings: {len(final_profile.enrollment_embeddings)}")
    print(f"Verified adaptive embeddings: {len(final_profile.verified_embeddings)}")
    
    print("\n7. TEACHER ROLLBACK")
    print("Rolling back to version 1...")
    profile_store.rollback_profile(student_id, 1)
    rolled_profile = profile_store.get_profile(student_id)
    print(f"Profile Version after rollback: {rolled_profile.profile_version}")
    print(f"Verified adaptive embeddings: {len(rolled_profile.verified_embeddings)}")
    
    print("\nDemonstration complete.")

if __name__ == "__main__":
    main()
