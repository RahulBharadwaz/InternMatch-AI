"""
Unit and Integration Tests for FAISS Vector Indexing Service
Validates IndexFlatIP, IndexHNSWFlat, incremental updates, persistence, and search latency.
"""
import os
import shutil
import tempfile
import numpy as np
import pytest

from app.services.vector_index import FAISSVectorIndex


@pytest.fixture
def sample_vectors():
    """Generate reproducible sample 384-dimensional unit vectors."""
    np.random.seed(42)
    dim = 384
    num_vectors = 10
    vecs = np.random.randn(num_vectors, dim).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


def test_faiss_index_flat_build_and_search(sample_vectors):
    """Test building exact IndexFlatIP and searching with query vector."""
    dim = sample_vectors.shape[1]
    opp_ids = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]

    index = FAISSVectorIndex(dimension=dim, index_type='flat')
    success = index.build_index(opp_ids, sample_vectors)
    assert success is True
    assert index.total_vectors == len(opp_ids)

    # Search with exact vector of opp 103 -> should return opp 103 as top result with similarity ~1.0
    query = sample_vectors[2]
    results = index.search(query, top_k=3)

    assert len(results) == 3
    top_opp_id, top_score = results[0]
    assert top_opp_id == 103
    assert top_score >= 0.999
    assert index.last_search_latency_ms < 10.0  # Must be fast


def test_faiss_index_hnsw_build_and_search(sample_vectors):
    """Test building graph-based IndexHNSWFlat."""
    dim = sample_vectors.shape[1]
    opp_ids = list(range(1, 11))

    index = FAISSVectorIndex(dimension=dim, index_type='hnsw')
    success = index.build_index(opp_ids, sample_vectors)
    assert success is True
    assert index.total_vectors == len(opp_ids)

    query = sample_vectors[5]
    results = index.search(query, top_k=5)
    assert len(results) == 5
    assert results[0][0] == 6  # opp_ids[5]
    assert results[0][1] >= 0.99


def test_faiss_add_or_update(sample_vectors):
    """Test incremental addition of new vectors."""
    dim = sample_vectors.shape[1]
    index = FAISSVectorIndex(dimension=dim, index_type='flat')
    index.build_index([1, 2], sample_vectors[:2])
    assert index.total_vectors == 2

    # Add a third vector
    index.add_or_update(3, sample_vectors[2])
    assert index.total_vectors == 3

    # Update existing vector
    index.add_or_update(1, sample_vectors[4])
    assert index.total_vectors == 3


def test_faiss_persistence(sample_vectors):
    """Test saving and loading vector index to/from disk."""
    temp_dir = tempfile.mkdtemp()
    try:
        dim = sample_vectors.shape[1]
        opp_ids = [201, 202, 203]
        orig_index = FAISSVectorIndex(dimension=dim, index_type='flat')
        orig_index.build_index(opp_ids, sample_vectors[:3])

        # Save to temp directory
        save_success = orig_index.save(temp_dir)
        assert save_success is True

        # Load into fresh index instance
        loaded_index = FAISSVectorIndex(dimension=dim, index_type='flat')
        load_success = loaded_index.load(temp_dir)
        assert load_success is True
        assert loaded_index.total_vectors == 3

        # Search loaded index
        query = sample_vectors[1]
        results = loaded_index.search(query, top_k=1)
        assert results[0][0] == 202
        assert results[0][1] >= 0.999
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_similarities_for_opportunities(sample_vectors):
    """Test ordered batch retrieval for specific opportunity IDs."""
    dim = sample_vectors.shape[1]
    opp_ids = [10, 20, 30]
    index = FAISSVectorIndex(dimension=dim, index_type='flat')
    index.build_index(opp_ids, sample_vectors[:3])

    query = sample_vectors[0]
    scores = index.get_similarities_for_opportunities(query, [30, 10, 999])

    assert len(scores) == 3
    assert scores[1] >= 0.999  # opp 10 is identical to query
    assert scores[2] == 0.5    # opp 999 is unknown, gets default neutral score

