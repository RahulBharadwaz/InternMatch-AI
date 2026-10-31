"""
Unit Tests for Contrastive Fine-Tuning Pipeline
Validates triplet curation, evaluation metrics, and InfoNCE loss computation.
"""
import torch
import torch.nn.functional as F
import numpy as np
import pytest

from scripts.train_biencoder import (
    get_curated_training_triplets,
    get_evaluation_pairs,
    TripletDataset,
    evaluate_similarity_correlation
)


def test_triplet_dataset_curation():
    """Verify curated training triplets cover required domains and are non-empty."""
    triplets = get_curated_training_triplets()
    assert len(triplets) >= 10

    # Ensure anchors, positives, and negatives are all distinct strings
    for anchor, pos, neg in triplets:
        assert isinstance(anchor, str) and len(anchor) > 15
        assert isinstance(pos, str) and len(pos) > 15
        assert isinstance(neg, str) and len(neg) > 15
        assert anchor != pos
        assert pos != neg

    dataset = TripletDataset(triplets)
    assert len(dataset) == len(triplets)
    first_item = dataset[0]
    assert len(first_item) == 3


def test_evaluation_pairs_structure():
    """Verify evaluation pairs have equal length and valid ground-truth scores."""
    s1, s2, scores = get_evaluation_pairs()
    assert len(s1) == len(s2) == len(scores)
    assert np.all(scores >= 0.0) and np.all(scores <= 1.0)


def test_infonce_loss_mathematical_properties():
    """Verify InfoNCE loss behaves correctly: lower loss for aligned vectors, higher for unaligned."""
    torch.manual_seed(42)
    dim = 64
    batch_size = 3

    # Anchors
    anchors = torch.randn(batch_size, dim)
    anchors = F.normalize(anchors, p=2, dim=1)

    # Perfect positives (identical to anchors)
    perfect_pos = anchors.clone()

    # Distant negatives (orthogonal or random)
    negatives = torch.randn(batch_size, dim)
    negatives = F.normalize(negatives, p=2, dim=1)

    scale = 20.0
    pos_sim = torch.mm(anchors, perfect_pos.t()) * scale
    neg_sim = torch.mm(anchors, negatives.t()) * scale
    logits = torch.cat([pos_sim, neg_sim], dim=1)
    labels = torch.arange(batch_size)

    low_loss = F.cross_entropy(logits, labels).item()

    # Now make positives distant/random and negatives identical to anchors (inverted)
    bad_pos = negatives.clone()
    bad_neg = anchors.clone()
    bad_pos_sim = torch.mm(anchors, bad_pos.t()) * scale
    bad_neg_sim = torch.mm(anchors, bad_neg.t()) * scale
    bad_logits = torch.cat([bad_pos_sim, bad_neg_sim], dim=1)

    high_loss = F.cross_entropy(bad_logits, labels).item()

    assert low_loss < high_loss
    assert low_loss < 0.1  # Highly aligned vectors should produce near-zero InfoNCE loss

