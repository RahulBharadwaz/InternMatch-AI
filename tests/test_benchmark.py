"""
Performance Benchmark Test
Measures recommendation inference latency and verifies sub-second SLA with embedding caching.
"""
import time
from datetime import date, timedelta
import pytest
from app import create_app
from app.extensions import db
from app.models import User, StudentProfile, EducationRecord, Organization, Opportunity
from app.services.recommendation_engine import RecommendationEngine


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_recommendation_latency_benchmark(app):
    """Verify recommendation inference latency stays under realistic SLAs."""
    org = Organization(name="Benchmark Org", sector="Information Technology")
    db.session.add(org)
    db.session.flush()

    user = User(email="bench.user@example.com", full_name="Bench User", role="student")
    user.set_password("Bench@123")
    db.session.add(user)
    db.session.flush()

    profile = StudentProfile(
        user_id=user.id,
        skills='["Python", "PyTorch", "Docker"]',
        preferred_location='Bangalore',
        completion_percentage=80
    )
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(profile_id=profile.id, highest_qualification='B.Tech', course='CS')
    db.session.add(edu)

    # Seed 10 realistic opportunities
    for i in range(10):
        opp = Opportunity(
            organization_id=org.id,
            title=f"Opportunity {i}: AI & Backend Intern",
            description=f"Working on ML pipelines, backend services, and Python systems {i}.",
            skills_required='["Python", "Docker"]',
            qualification_required='B.Tech',
            location='Bangalore',
            is_published=True,
            application_deadline=date.today() + timedelta(days=30)
        )
        db.session.add(opp)
    db.session.commit()

    engine = RecommendationEngine()

    # Warm-up run (loads model and computes initial embeddings)
    t0 = time.time()
    rec_id_warmup = engine.generate_recommendations(user.id)
    warmup_time = time.time() - t0
    assert rec_id_warmup is not None

    # Benchmark cached inference run
    t1 = time.time()
    rec_id_cached = engine.generate_recommendations(user.id)
    cached_latency = time.time() - t1
    assert rec_id_cached is not None

    print(f"\n[Benchmark] Warmup run: {warmup_time*1000:.1f}ms | Cached inference: {cached_latency*1000:.1f}ms")

    # Cached recommendation run should complete in under 500ms on CPU
    assert cached_latency < 0.50, f"Cached inference took too long: {cached_latency*1000:.1f}ms"

