"""
Evaluation and Benchmarking Module for InternMatch Recommendation Engine
Calculates standard information retrieval and ranking metrics:
- Precision@K
- Recall@K
- MRR@K (Mean Reciprocal Rank)
- NDCG@K (Normalized Discounted Cumulative Gain)
Supports ground-truth evaluation across TF-IDF Baseline, Sentence-BERT Semantic, and Hybrid Matcher.
"""
import math
from typing import List, Dict, Any, Tuple


class RankingEvaluator:
    """Computes ranking and information retrieval metrics against ground truth."""

    @staticmethod
    def precision_at_k(recommended_ids: List[int], relevant_ids: set, k: int) -> float:
        """
        Compute Precision@K.
        Fraction of top-K recommended items that are relevant.
        """
        if k <= 0:
            return 0.0
        top_k = recommended_ids[:k]
        if not top_k:
            return 0.0
        relevant_in_top_k = sum(1 for item in top_k if item in relevant_ids)
        return relevant_in_top_k / k

    @staticmethod
    def recall_at_k(recommended_ids: List[int], relevant_ids: set, k: int) -> float:
        """
        Compute Recall@K.
        Fraction of all relevant items that were successfully recommended in top-K.
        """
        if not relevant_ids or k <= 0:
            return 0.0
        top_k = recommended_ids[:k]
        relevant_in_top_k = sum(1 for item in top_k if item in relevant_ids)
        return relevant_in_top_k / len(relevant_ids)

    @staticmethod
    def mean_reciprocal_rank_at_k(recommended_ids: List[int], relevant_ids: set, k: int) -> float:
        """
        Compute Reciprocal Rank at K.
        1 / rank of the first relevant item in the recommendation list (within top-K), or 0.0.
        """
        for rank, item in enumerate(recommended_ids[:k], 1):
            if item in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(recommended_ids: List[int], ground_truth_relevance: Dict[int, int], k: int) -> float:
        """
        Compute Normalized Discounted Cumulative Gain at K (NDCG@K) with graded relevance.
        Gain formulation: (2^rel - 1) / log2(rank + 1).
        """
        if k <= 0 or not ground_truth_relevance:
            return 0.0

        # Compute DCG@K
        dcg = 0.0
        for rank, item in enumerate(recommended_ids[:k], 1):
            rel = ground_truth_relevance.get(item, 0)
            if rel > 0:
                dcg += (2.0 ** rel - 1.0) / math.log2(rank + 1.0)

        # Compute Ideal DCG@K (sorted descending by true relevance)
        ideal_relevances = sorted(ground_truth_relevance.values(), reverse=True)
        idcg = 0.0
        for rank, rel in enumerate(ideal_relevances[:k], 1):
            if rel > 0:
                idcg += (2.0 ** rel - 1.0) / math.log2(rank + 1.0)

        if idcg == 0.0:
            return 0.0
        return dcg / idcg

    @classmethod
    def evaluate_ranking(cls, recommended_ids: List[int], ground_truth_relevance: Dict[int, int],
                         ks: List[int] = [3, 5]) -> Dict[str, float]:
        """Compute all ranking metrics for a single query."""
        relevant_set = {opp_id for opp_id, rel in ground_truth_relevance.items() if rel >= 1}
        metrics = {}
        for k in ks:
            metrics[f'P@{k}'] = cls.precision_at_k(recommended_ids, relevant_set, k)
            metrics[f'R@{k}'] = cls.recall_at_k(recommended_ids, relevant_set, k)
            metrics[f'NDCG@{k}'] = cls.ndcg_at_k(recommended_ids, ground_truth_relevance, k)
            metrics[f'MRR@{k}'] = cls.mean_reciprocal_rank_at_k(recommended_ids, relevant_set, k)
        return metrics

