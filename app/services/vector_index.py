"""
FAISS Vector Index Service for High-Performance Nearest Neighbor Retrieval
Provides IndexFlatIP and IndexHNSWFlat indexing for dense 384-dimensional
Sentence-BERT embeddings with sub-millisecond similarity search and persistence.
"""
import os
import json
import time
import logging
from typing import List, Tuple, Dict, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS is not installed. Falling back to NumPy dot-product vector search.")


class FAISSVectorIndex:
    """
    Production-grade FAISS vector index manager for dense semantic embeddings.
    Supports both exact inner product (IndexFlatIP) and graph-based ANN (IndexHNSWFlat).
    """

    def __init__(self, dimension: int = 384, index_type: str = 'flat', hnsw_m: int = 32):
        """
        Initialize vector index.

        Args:
            dimension: Dimensionality of embeddings (default 384 for all-MiniLM-L6-v2).
            index_type: 'flat' (exact IndexFlatIP) or 'hnsw' (approximate IndexHNSWFlat).
            hnsw_m: Number of bi-directional links per node in HNSW graph.
        """
        self.dimension = dimension
        self.index_type = index_type.lower()
        self.hnsw_m = hnsw_m
        self.index: Optional[Any] = None
        
        # Mapping from FAISS internal integer position -> Opportunity ID
        self.internal_to_opp_id: Dict[int, int] = {}
        # Mapping from Opportunity ID -> FAISS internal integer position
        self.opp_id_to_internal: Dict[int, int] = {}
        # Cache of stored vectors for rebuilds/updates: opp_id -> vector (float32, 1D)
        self.vectors_cache: Dict[int, np.ndarray] = {}
        
        self.last_search_latency_ms: float = 0.0
        self._initialize_index()

    def _initialize_index(self):
        """Initialize empty FAISS index."""
        if not FAISS_AVAILABLE:
            return

        if self.index_type == 'hnsw':
            # Inner product metric with HNSW graph indexing for fast ANN
            self.index = faiss.IndexHNSWFlat(self.dimension, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)
            self.index.hnsw.efSearch = 64
            self.index.hnsw.efConstruction = 64
        else:
            # Exact inner product (equivalent to cosine similarity on unit-normalized vectors)
            self.index = faiss.IndexFlatIP(self.dimension)

        self.internal_to_opp_id.clear()
        self.opp_id_to_internal.clear()

    @staticmethod
    def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
        """L2-normalize vectors for cosine similarity computation via inner product."""
        vectors = vectors.astype(np.float32)
        if len(vectors.shape) == 1:
            norm = np.linalg.norm(vectors)
            if norm > 0:
                return vectors / norm
            return vectors
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def build_index(self, opportunity_ids: List[int], embeddings: np.ndarray) -> bool:
        """
        Build or rebuild the FAISS index from an array of embeddings.

        Args:
            opportunity_ids: List of database Opportunity IDs.
            embeddings: 2D NumPy array of shape (N, dimension).

        Returns:
            bool: True if index was successfully built.
        """
        if len(opportunity_ids) == 0:
            logger.info("No opportunity vectors provided to build FAISS index.")
            return False

        if len(opportunity_ids) != len(embeddings):
            raise ValueError(f"Mismatch: {len(opportunity_ids)} IDs vs {len(embeddings)} vectors.")

        norm_embeddings = self._normalize_vectors(embeddings)
        self._initialize_index()

        self.vectors_cache.clear()
        for idx, opp_id in enumerate(opportunity_ids):
            self.internal_to_opp_id[idx] = opp_id
            self.opp_id_to_internal[opp_id] = idx
            self.vectors_cache[opp_id] = norm_embeddings[idx]

        if FAISS_AVAILABLE and self.index is not None:
            self.index.add(norm_embeddings)
            logger.info("Built FAISS (%s) index with %d items.", self.index_type, self.index.ntotal)
            return True
        return False

    def add_or_update(self, opp_id: int, embedding: np.ndarray) -> bool:
        """
        Add or update an individual opportunity vector. Rebuilds index to keep contiguous IDs.

        Args:
            opp_id: Opportunity ID.
            embedding: 1D NumPy array of dimension 384.

        Returns:
            bool: True if added/updated successfully.
        """
        norm_vec = self._normalize_vectors(embedding)
        self.vectors_cache[opp_id] = norm_vec

        # Re-index stored vectors
        all_ids = list(self.vectors_cache.keys())
        all_vecs = np.vstack([self.vectors_cache[i] for i in all_ids])
        return self.build_index(all_ids, all_vecs)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for top-k closest opportunities given a query embedding.

        Args:
            query_embedding: 1D or 2D array of query vector.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            List of (opportunity_id, similarity_score) sorted by highest similarity first.
        """
        start_time = time.perf_counter()
        
        if query_embedding.ndim == 1:
            query_vec = query_embedding.reshape(1, -1)
        else:
            query_vec = query_embedding

        query_vec = self._normalize_vectors(query_vec)
        results: List[Tuple[int, float]] = []

        if FAISS_AVAILABLE and self.index is not None and self.index.ntotal > 0:
            actual_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_vec, actual_k)

            for internal_id, dist in zip(indices[0], distances[0]):
                if internal_id in self.internal_to_opp_id:
                    opp_id = self.internal_to_opp_id[internal_id]
                    # Map cosine from [-1, 1] to [0, 1]
                    normalized_score = float(max(0.0, min(1.0, (dist + 1.0) / 2.0 if dist < 0 else dist)))
                    results.append((opp_id, normalized_score))
        elif self.vectors_cache:
            # Fallback NumPy cosine similarity
            all_ids = list(self.vectors_cache.keys())
            matrix = np.vstack([self.vectors_cache[i] for i in all_ids])
            sims = np.dot(matrix, query_vec.flatten())
            sorted_indices = np.argsort(sims)[::-1][:top_k]
            for s_idx in sorted_indices:
                opp_id = all_ids[s_idx]
                sim = sims[s_idx]
                normalized_score = float(max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim)))
                results.append((opp_id, normalized_score))

        self.last_search_latency_ms = (time.perf_counter() - start_time) * 1000.0
        return results

    def get_similarities_for_opportunities(self, query_embedding: np.ndarray,
                                           opportunity_ids: List[int]) -> List[float]:
        """
        Calculate semantic similarity for a specific ordered list of opportunities.
        Uses FAISS vectors when available, with sub-millisecond execution.
        """
        start_time = time.perf_counter()
        query_vec = self._normalize_vectors(query_embedding).flatten()
        
        scores: List[float] = []
        for opp_id in opportunity_ids:
            if opp_id in self.vectors_cache:
                vec = self.vectors_cache[opp_id]
                raw_dot = float(np.dot(vec, query_vec))
                score = float(max(0.0, min(1.0, (raw_dot + 1.0) / 2.0 if raw_dot < 0 else raw_dot)))
            else:
                score = 0.5  # Neutral default
            scores.append(score)

        self.last_search_latency_ms = (time.perf_counter() - start_time) * 1000.0
        return scores

    def save(self, directory_path: str) -> bool:
        """
        Persist the FAISS index and ID mapping dictionary to disk.

        Args:
            directory_path: Directory where index.faiss and metadata.json are saved.
        """
        os.makedirs(directory_path, exist_ok=True)
        index_file = os.path.join(directory_path, 'index.faiss')
        meta_file = os.path.join(directory_path, 'metadata.json')

        try:
            if FAISS_AVAILABLE and self.index is not None:
                faiss.write_index(self.index, index_file)

            meta = {
                'dimension': self.dimension,
                'index_type': self.index_type,
                'internal_to_opp_id': {str(k): v for k, v in self.internal_to_opp_id.items()},
                'opp_id_to_internal': {str(k): v for k, v in self.opp_id_to_internal.items()},
                'cached_ids': list(self.vectors_cache.keys())
            }
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)

            # Save vectors numpy archive
            if self.vectors_cache:
                vecs_file = os.path.join(directory_path, 'vectors.npz')
                np.savez_compressed(vecs_file, **{str(k): v for k, v in self.vectors_cache.items()})

            logger.info("Saved FAISS index to %s", directory_path)
            return True
        except Exception as e:
            logger.error("Failed to save FAISS index: %s", e)
            return False

    def load(self, directory_path: str) -> bool:
        """
        Load a persisted FAISS index and ID mapping dictionary from disk.
        """
        index_file = os.path.join(directory_path, 'index.faiss')
        meta_file = os.path.join(directory_path, 'metadata.json')
        vecs_file = os.path.join(directory_path, 'vectors.npz')

        if not os.path.exists(meta_file):
            return False

        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            self.dimension = meta.get('dimension', 384)
            self.index_type = meta.get('index_type', 'flat')
            self.internal_to_opp_id = {int(k): v for k, v in meta.get('internal_to_opp_id', {}).items()}
            self.opp_id_to_internal = {int(k): v for k, v in meta.get('opp_id_to_internal', {}).items()}

            if os.path.exists(vecs_file):
                with np.load(vecs_file) as data:
                    self.vectors_cache = {int(k): data[k] for k in data.files}

            if FAISS_AVAILABLE and os.path.exists(index_file):
                self.index = faiss.read_index(index_file)
                logger.info("Loaded FAISS index from %s with %d items.", directory_path, self.index.ntotal)
            else:
                self._initialize_index()
                if self.vectors_cache:
                    all_ids = list(self.vectors_cache.keys())
                    all_vecs = np.vstack([self.vectors_cache[i] for i in all_ids])
                    self.build_index(all_ids, all_vecs)

            return True
        except Exception as e:
            logger.error("Failed to load FAISS index: %s", e)
            return False

    @property
    def total_vectors(self) -> int:
        """Return total number of vectors in index."""
        if FAISS_AVAILABLE and self.index is not None:
            return self.index.ntotal
        return len(self.vectors_cache)

