"""
Unit tests for RankingEvaluator
Validates mathematical correctness of Precision@K, Recall@K, NDCG@K, and MRR@K.
"""
import pytest
from app.services.evaluation import RankingEvaluator


def test_precision_at_k():
    recs = [1, 2, 3, 4, 5]
    relevant = {1, 3, 7}

    # In top-3: items 1, 2, 3 -> items 1 and 3 are relevant -> P@3 = 2/3
    p3 = RankingEvaluator.precision_at_k(recs, relevant, 3)
    assert abs(p3 - (2.0 / 3.0)) < 1e-4

    # In top-5: items 1, 2, 3, 4, 5 -> items 1 and 3 are relevant -> P@5 = 2/5 = 0.4
    p5 = RankingEvaluator.precision_at_k(recs, relevant, 5)
    assert abs(p5 - 0.4) < 1e-4


def test_recall_at_k():
    recs = [1, 2, 3, 4, 5]
    relevant = {1, 3, 7}  # 3 total relevant items in ground truth

    # In top-3: found 2 out of 3 -> R@3 = 2/3
    r3 = RankingEvaluator.recall_at_k(recs, relevant, 3)
    assert abs(r3 - (2.0 / 3.0)) < 1e-4

    # In top-5: found 2 out of 3 -> R@5 = 2/3
    r5 = RankingEvaluator.recall_at_k(recs, relevant, 5)
    assert abs(r5 - (2.0 / 3.0)) < 1e-4


def test_mrr_at_k():
    # First relevant item is at rank 1 -> MRR = 1.0
    assert RankingEvaluator.mean_reciprocal_rank_at_k([10, 20, 30], {10}, 3) == 1.0

    # First relevant item is at rank 2 -> MRR = 0.5
    assert RankingEvaluator.mean_reciprocal_rank_at_k([99, 10, 30], {10}, 3) == 0.5

    # No relevant items in top-3 -> MRR = 0.0
    assert RankingEvaluator.mean_reciprocal_rank_at_k([99, 88, 77], {10}, 3) == 0.0


def test_ndcg_at_k_perfect_ranking():
    # If recommended items are in perfect relevance order, NDCG should be 1.0
    recs = [1, 2, 3]
    relevance = {1: 2, 2: 1, 3: 0}
    ndcg = RankingEvaluator.ndcg_at_k(recs, relevance, 3)
    assert abs(ndcg - 1.0) < 1e-4


def test_ndcg_at_k_suboptimal_ranking():
    # Swapped relevance order
    recs = [2, 1, 3]
    relevance = {1: 2, 2: 1, 3: 0}
    ndcg = RankingEvaluator.ndcg_at_k(recs, relevance, 3)
    assert 0.0 < ndcg < 1.0


def test_empty_and_zero_k_edge_cases():
    assert RankingEvaluator.precision_at_k([], {1, 2}, 3) == 0.0
    assert RankingEvaluator.precision_at_k([1, 2], {1, 2}, 0) == 0.0
    assert RankingEvaluator.recall_at_k([1, 2], set(), 3) == 0.0
    assert RankingEvaluator.ndcg_at_k([], {}, 3) == 0.0

