import os
import pickle
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import re

# Load embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_paths(domain):
    base = domain.replace("https://", "").replace("http://", "").replace("/", "_")
    faiss_path = os.path.join(CACHE_DIR, f"{base}_faiss.index")
    bm25_path = os.path.join(CACHE_DIR, f"{base}_bm25.pkl")
    chunks_path = os.path.join(CACHE_DIR, f"{base}_chunks.pkl")
    return faiss_path, bm25_path, chunks_path

class HybridRetriever:
    def __init__(self, text: str, domain: str, chunk_size: int = 3):
        self.domain = domain
        self.chunk_size = chunk_size

        faiss_path, bm25_path, chunks_path = get_cache_paths(domain)

        if os.path.exists(faiss_path) and os.path.exists(bm25_path) and os.path.exists(chunks_path):
            self.faiss_index = faiss.read_index(faiss_path)
            with open(bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)
            with open(chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
        else:
            self.chunks = self.chunk_text(text)
            # Build BM25 from all chunks
            self.bm25 = BM25Okapi([chunk.split() for chunk in self.chunks])
            # Build FAISS index from chunk embeddings
            self.faiss_index, _ = self.build_faiss(self.chunks)

            faiss.write_index(self.faiss_index, faiss_path)
            with open(bm25_path, "wb") as f:
                pickle.dump(self.bm25, f)
            with open(chunks_path, "wb") as f:
                pickle.dump(self.chunks, f)

    def chunk_text(self, text: str):
        # Try sentence-based splitting
        sentences = re.split(r'(?<=[.!?]) +', text)

        if len(sentences) < self.chunk_size:
            # Fallback to word-based chunks
            words = text.split()
            chunks = [
                " ".join(words[i:i + self.chunk_size * 20])
                for i in range(0, len(words), self.chunk_size * 20)
            ]
        else:
            chunks = [
                " ".join(sentences[i:i + self.chunk_size])
                for i in range(0, len(sentences), self.chunk_size)
            ]

        # Filter out empty or whitespace-only chunks
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def build_faiss(self, chunks):
        embeddings = embedding_model.encode(chunks)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(embeddings))
        return index, embeddings

    def search(self, query: str, top_k: int = 5, mix_ratio: float = 0.5):
        """
        Hybrid search: merges FAISS (semantic) scores and BM25 (keyword) scores.
        By default, we only do top_k on the FAISS side for efficiency,
        but consider *all* BM25 chunk scores. 
        """
        # Encode the query
        query_embedding = embedding_model.encode([query])[0]

        # --- 1) Get FAISS top_k ---
        D, I = self.faiss_index.search(np.array([query_embedding]), top_k)
        # Convert distances into "faiss scores"
        # We'll do 1 / (1 + distance) so that lower distance => higher score
        faiss_scores = {i: 1.0 / (1.0 + D[0][j]) for j, i in enumerate(I[0])}

        # --- 2) Compute BM25 scores for *all* chunks ---
        bm25_scores_array = self.bm25.get_scores(query.split())
        bm25_scores_dict = {i: score for i, score in enumerate(bm25_scores_array)}

        # --- 3) Merge scores for the *union* of all chunk IDs from either method ---
        # We'll just iterate over all chunk IDs from 0..len(self.chunks)-1
        # so that we don't ignore chunks that might have a decent BM25 or FAISS score
        merged_scores = {}
        for i in range(len(self.chunks)):
            faiss_score = faiss_scores.get(i, 0.0)
            bm25_score = bm25_scores_dict.get(i, 0.0)
            merged = mix_ratio * faiss_score + (1.0 - mix_ratio) * bm25_score

            # If you want to exclude chunks that have effectively zero from both, 
            # you can do:
            if merged > 0:
                merged_scores[i] = merged

        # --- 4) Sort by merged score and pick top_k overall ---
        top_hits = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Return the text for those chunk IDs
        return [self.chunks[i] for i, _ in top_hits]
