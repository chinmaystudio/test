import faiss
import numpy as np
import json
import os
from uuid import UUID

class LocalDatabase:
    """
    FAISS + JSON metadata for local development.
    """
    def __init__(self, index_path="data/faiss_index.bin", meta_path="data/metadata.json"):
        import os
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.index_path = index_path
        self.meta_path = meta_path
        self.dimension = 512 # ArcFace embedding size
        
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            # Using Inner Product for cosine similarity (assuming normalized embeddings)
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = {} # faiss_id -> metadata dict
            
    def add_embedding(self, embedding, metadata):
        faiss_id = self.index.ntotal
        # Ensure embedding is 2D and float32
        emb = np.array([embedding], dtype=np.float32)
        self.index.add(emb)
        self.metadata[str(faiss_id)] = metadata
        self.save()
        return faiss_id
        
    def search(self, embedding, k=1, classroom_id=None):
        """Single embedding search (legacy)."""
        res = self.search_batch([embedding], k, classroom_id)
        return res[0] if res else []

    def search_batch(self, embeddings, k=1, classroom_id=None):
        """Batch search for multiple query embeddings simultaneously."""
        if self.index.ntotal == 0 or not embeddings:
            return [[] for _ in embeddings]
            
        emb_arr = np.array(embeddings, dtype=np.float32)
        distances, indices = self.index.search(emb_arr, k * 5)
        
        batch_results = []
        for q_idx in range(len(embeddings)):
            results = []
            for i, idx in enumerate(indices[q_idx]):
                if idx == -1: continue
                meta = self.metadata.get(str(idx))
                if not meta: continue
                
                if classroom_id and meta.get('classroom_id') != classroom_id:
                    continue

                # Legacy local indexes may contain aliases from benchmark runs.
                # Never return those as canonical attendance identities.
                try:
                    canonical_student_id = str(UUID(str(meta.get('student_id'))))
                except (TypeError, ValueError, AttributeError):
                    continue

                results.append({
                    'similarity': float(distances[q_idx][i]),
                    'student_id': canonical_student_id,
                    'name': meta.get('name'),
                    'classroom_id': meta.get('classroom_id')
                })
                
                if len(results) >= k:
                    break
            batch_results.append(results)
            
        return batch_results
        
    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'w') as f:
            json.dump(self.metadata, f)
