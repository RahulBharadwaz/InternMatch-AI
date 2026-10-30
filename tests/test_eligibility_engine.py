"""
Unit tests for EligibilityEngine service
Validates qualification hierarchy, age evaluation from DOB, and employment status rules.
"""
import json
from datetime import date, timedelta
import pytest
from app import create_app
from app.extensions import db
from app.models import User, StudentProfile, EducationRecord, EligibilityRule
from app.services.eligibility_engine import EligibilityEngine


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def setup_rules(app):
    """Seed standard PMIS eligibility rules."""
    rules = [
        EligibilityRule(
            name='Qualification Requirement',
            rule_type='qualification',
            condition=json.dumps({'min_level': 'bachelor'}),
            is_mandatory=True,
            is_active=True
        ),
        EligibilityRule(
            name='Age Limit Requirement',
            rule_type='age',
            condition=json.dumps({'min_age': 21, 'max_age': 24}),
            is_mandatory=True,
            is_active=True
        ),
        EligibilityRule(
            name='Employment Status Requirement',
            rule_type='employment_status',
            condition=json.dumps({'employed': False}),
            is_mandatory=True,
            is_active=True
        ),
        EligibilityRule(
            name='Inactive Advisory Rule',
            rule_type='qualification',
            condition=json.dumps({'min_level': 'master'}),
            is_mandatory=False,
            is_active=False
        )
    ]
    db.session.add_all(rules)
    db.session.commit()
    return rules


def test_fully_eligible_candidate(app, setup_rules):
    """Verify candidate meeting all requirements gets 'eligible' status."""
    user = User(email="eligible@example.com", full_name="Eligible Candidate")
    user.set_password("Pass@123")
    db.session.add(user)
    db.session.flush()

    # Age 22
    dob = date.today() - timedelta(days=22 * 365 + 10)
    profile = StudentProfile(
        user_id=user.id,
        date_of_birth=dob,
        employment_status='unemployed'
    )
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='B.Tech',
        course='Computer Science'
    )
    db.session.add(edu)
    db.session.commit()

    engine = EligibilityEngine()
    result = engine.evaluate_student(user.id)
    assert result['overall_status'] == 'eligible'
    assert result['eligible'] is True
    assert len(result['mandatory_failures']) == 0


def test_age_out_of_bounds_fails(app, setup_rules):
    """Verify candidate under or over age range fails age rule."""
    user = User(email="overage@example.com", full_name="Older Candidate")
    user.set_password("Pass@123")
    db.session.add(user)
    db.session.flush()

    # Age 27 (exceeds max_age 24)
    dob = date.today() - timedelta(days=27 * 365 + 50)
    profile = StudentProfile(
        user_id=user.id,
        date_of_birth=dob,
        employment_status='unemployed'
    )
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='B.Tech',
        course='Information Technology'
    )
    db.session.add(edu)
    db.session.commit()

    engine = EligibilityEngine()
    result = engine.evaluate_student(user.id)
    assert result['overall_status'] == 'ineligible'
    assert result['eligible'] is False
    assert any('Age Limit Requirement' in f['rule'] for f in result['mandatory_failures'])


def test_employed_candidate_fails(app, setup_rules):
    """Verify employed candidate fails employment status rule."""
    user = User(email="employed@example.com", full_name="Employed Candidate")
    user.set_password("Pass@123")
    db.session.add(user)
    db.session.flush()

    dob = date.today() - timedelta(days=23 * 365)
    profile = StudentProfile(
        user_id=user.id,
        date_of_birth=dob,
        employment_status='employed'
    )
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='B.Tech',
        course='ECE'
    )
    db.session.add(edu)
    db.session.commit()

    engine = EligibilityEngine()
    result = engine.evaluate_student(user.id)
    assert result['overall_status'] == 'ineligible'
    assert any('Employment Status Requirement' in f['rule'] for f in result['mandatory_failures'])


def test_missing_dob_returns_insufficient_info(app, setup_rules):
    """Verify missing DOB returns 'insufficient_info' overall status."""
    user = User(email="nodob@example.com", full_name="No DOB Candidate")
    user.set_password("Pass@123")
    db.session.add(user)
    db.session.flush()

    profile = StudentProfile(
        user_id=user.id,
        date_of_birth=None,  # Missing
        employment_status='unemployed'
    )
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='B.Tech',
        course='Computer Science'
    )
    db.session.add(edu)
    db.session.commit()

    engine = EligibilityEngine()
    result = engine.evaluate_student(user.id)
    assert result['overall_status'] == 'insufficient_info'
    assert any('Age Limit Requirement' in item['rule'] for item in result['insufficient_info'])


def test_diploma_fails_bachelor_requirement(app, setup_rules):
    """Verify candidate with only Diploma fails bachelor minimum requirement."""
    user = User(email="diploma@example.com", full_name="Diploma Candidate")
    user.set_password("Pass@123")
    db.session.add(user)
    db.session.flush()

    dob = date.today() - timedelta(days=22 * 365)
    profile = StudentProfile(user_id=user.id, date_of_birth=dob, employment_status='student')
    db.session.add(profile)
    db.session.flush()

    edu = EducationRecord(
        profile_id=profile.id,
        highest_qualification='Diploma',
        course='Mechanical Polytechnic'
    )
    db.session.add(edu)
    db.session.commit()

    engine = EligibilityEngine()
    result = engine.evaluate_student(user.id)
    assert result['overall_status'] == 'ineligible'
    assert any('Qualification Requirement' in f['rule'] for f in result['mandatory_failures'])

