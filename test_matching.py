import numpy as np
from core.matching import ThresholdPolicy, MatchState
from db.database import LocalDatabase
import os

db = LocalDatabase()
print(f"Total embeddings in DB: {db.index.ntotal}")
if db.index.ntotal > 0:
    # Get the first embedding
    # We can't easily extract the vector from IndexFlatIP, but we can simulate a search
    # Let's just create a random normalized embedding
    emb = np.random.randn(512).astype(np.float32)
    emb = emb / np.linalg.norm(emb)
    
    matches = db.search_batch([emb], k=1, classroom_id=None)
    print("Random search matches:", matches)
    
    # What if we search for a zero vector?
    zero_emb = np.zeros(512, dtype=np.float32)
    matches_zero = db.search_batch([zero_emb], k=1, classroom_id=None)
    print("Zero search matches:", matches_zero)
else:
    print("DB is empty. Creating a dummy entry.")
    emb = np.random.randn(512).astype(np.float32)
    emb = emb / np.linalg.norm(emb)
    db.add_embedding(emb, {"student_id": "00000000-0000-0000-0000-000000000000", "classroom_id": "test", "name": "Test"})
    matches = db.search_batch([emb], k=1, classroom_id=None)
    print("Self search matches:", matches)

policy = ThresholdPolicy()
print("Policy decide on None:", policy.decide(None))
print("Policy decide on 0.0:", policy.decide({"similarity": 0.0, "student_id": "test"}))
print("Policy decide on 0.4:", policy.decide({"similarity": 0.4, "student_id": "test"}))
print("Policy decide on 0.5:", policy.decide({"similarity": 0.5, "student_id": "test"}))
print("Policy decide on 0.6:", policy.decide({"similarity": 0.6, "student_id": "test"}))
