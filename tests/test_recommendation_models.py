"""
Unit tests for Recommendation Models & Hybrid Engine
Validates TF-IDF baseline, Sentence-BERT semantic matching, embedding caching,
hybrid scoring, missing skill tracking, and deadline filtering.
"""
from datetime import date, timedelta
import json
import pytest
from app import create_app
from app.extensions import db
from app.models import (
    User, StudentProfile, EducationRecord, StudentSkill, Skill,
    Organization, Opportunity, Recommendation, RecommendationItem
)
from app.services.recommendation_engine import (
    RecommendationEngine, get_sbert_model, _OPPORTUNITY_EMBEDDING_CACHE
)


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def setup_dataset(app):
    """Seed test opportunities and candidate for model testing."""
    # Organization
    org = Organization(name="GovTech Research Lab", sector="Information Technology")
    db.session.add(org)
    db.session.flush()

    # User
    user = User(email="ml.student@example.com", full_name="ML Student", role="student")
    user.set_password("Student@123")
    db.session.add(user)
    db.session.flush()

    # Profile
    profile = StudentProfile(
        user_id=user.id,
        preferred_industries='["Information Technology"]',
        preferred_domains='["Artificial Intelligence"]',
        preferred_roles='["ML Engineer"]',
        preferred_location='Bangalore',
        relocation_preference='yes',
        skills='["Python", "PyTorch", "Docker"]',
        completion_percentage=85
    )
    db.session.add(profile)
    db.session.flush()

    # Education
    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='B.Tech',
        course='Computer Science & Engineering'
    )
    db.session.add(edu)

    # Opportunity 1: Highly aligned ML role
    opp1 = Opportunity(
        organization_id=org.id,
        title='Deep Learning & AI Intern',
        description='Design neural networks in PyTorch for computer vision and NLP models.',
        skills_required='["Python", "PyTorch", "Computer Vision", "Docker"]',
        qualification_required='B.Tech Computer Science',
        location='Bangalore',
        domain='Artificial Intelligence',
        role_type='ML Engineer',
        application_deadline=date.today() + timedelta(days=20),
        is_published=True
    )
    db.session.add(opp1)

    # Opportunity 2: Unaligned Marketing role
    opp2 = Opportunity(
        organization_id=org.id,
        title='Digital Marketing Intern',
        description='SEO, social media campaigns, content strategy, and public relations.',
        skills_required='["Digital Marketing", "Market Research", "Excel"]',
        qualification_required='BBA / B.Com',
        location='Delhi',
        domain='Marketing',
        role_type='Marketing Specialist',
        application_deadline=date.today() + timedelta(days=20),
        is_published=True
    )
    db.session.add(opp2)

    # Opportunity 3: Expired opportunity
    opp3 = Opportunity(
        organization_id=org.id,
        title='Expired Python Opportunity',
        description='Python development intern.',
        skills_required='["Python"]',
        qualification_required='B.Tech',
        location='Bangalore',
        domain='Artificial Intelligence',
        role_type='ML Engineer',
        application_deadline=date.today() - timedelta(days=2),
        is_published=True
    )
    db.session.add(opp3)

    db.session.commit()
    return user.id, opp1.id, opp2.id, opp3.id


def test_sbert_model_singleton():
    """Verify Sentence-BERT model loads as a singleton."""
    model1 = get_sbert_model()
    model2 = get_sbert_model()
    assert model1 is not None
    assert model1 is model2


def test_embedding_caching_behavior(app, setup_dataset):
    """Verify opportunity embeddings are cached and reused to prevent latency spikes."""
    user_id, opp1_id, opp2_id, opp3_id = setup_dataset
    engine = RecommendationEngine()

    _OPPORTUNITY_EMBEDDING_CACHE.clear()

    # First run computes embeddings and populates cache
    rec_id1 = engine.generate_recommendations(user_id)
    assert opp1_id in _OPPORTUNITY_EMBEDDING_CACHE
    assert opp2_id in _OPPORTUNITY_EMBEDDING_CACHE
    cached_ts1, emb1 = _OPPORTUNITY_EMBEDDING_CACHE[opp1_id]

    # Second run should reuse the cached embedding without recomputing
    rec_id2 = engine.generate_recommendations(user_id)
    cached_ts2, emb2 = _OPPORTUNITY_EMBEDDING_CACHE[opp1_id]

    assert cached_ts1 == cached_ts2
    assert emb1 is emb2


def test_hybrid_ranking_order_and_closed_exclusion(app, setup_dataset):
    """Verify aligned ML opportunity ranks above marketing, and closed opp is excluded."""
    user_id, opp1_id, opp2_id, opp3_id = setup_dataset
    engine = RecommendationEngine()

    rec_id = engine.generate_recommendations(user_id)
    assert rec_id is not None

    items = RecommendationItem.query.filter_by(recommendation_id=rec_id).order_by(RecommendationItem.rank).all()
    # Expired opp3 must NOT be in recommendations
    item_opp_ids = [item.opportunity_id for item in items]
    assert opp3_id not in item_opp_ids

    # Opp1 (AI/ML) must rank #1 above Opp2 (Marketing)
    assert items[0].opportunity_id == opp1_id
    assert items[0].match_score > items[1].match_score
    assert items[0].semantic_score > items[1].semantic_score
    assert items[0].skills_score > items[1].skills_score


def test_missing_and_matching_skills_tracking(app, setup_dataset):
    """Verify matching skills (Python, PyTorch, Docker) and missing skill (Computer Vision)."""
    user_id, opp1_id, opp2_id, opp3_id = setup_dataset
    engine = RecommendationEngine()

    rec_id = engine.generate_recommendations(user_id)
    top_item = RecommendationItem.query.filter_by(
        recommendation_id=rec_id,
        opportunity_id=opp1_id
    ).first()

    matched = json.loads(top_item.matching_skills)
    missing = json.loads(top_item.missing_skills)

    assert "Python" in matched
    assert "PyTorch" in matched
    assert "Docker" in matched
    assert "Computer Vision" in missing


def test_weights_sum_to_one(app):
    """Verify recommendation weights are normalized to sum to 1.0."""
    engine = RecommendationEngine()
    total_weight = sum(engine.weights.values())
    assert abs(total_weight - 1.0) < 1e-5
