"""
Tests for recommendation engine
"""
import pytest
import json
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import (
    User, StudentProfile, EducationRecord, StudentSkill, Skill, Opportunity,
    Organization, Resume, ResumeExtraction, RecommendationItem
)
from app.services.recommendation_engine import RecommendationEngine
from app.services.resume_parser import ResumeParser

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def setup_data(app):
    """Setup test data"""
    with app.app_context():
        # Create user
        user = User(
            email='test@example.com',
            full_name='Test User',
            role='student'
        )
        user.set_password('Test@123')
        db.session.add(user)
        db.session.flush()
        
        # Create profile
        profile = StudentProfile(
            user_id=user.id,
            preferred_industries='["Information Technology"]',
            preferred_domains='["Web Development"]',
            preferred_location='Bangalore',
            completion_percentage=50
        )
        db.session.add(profile)
        db.session.flush()
        
        # Create skills
        skill1 = Skill(name='Python', category='technical')
        skill2 = Skill(name='JavaScript', category='technical')
        db.session.add(skill1)
        db.session.add(skill2)
        db.session.flush()
        
        # Add user skills
        user_skill = StudentSkill(
            user_id=user.id,
            skill_id=skill1.id,
            proficiency_level='intermediate'
        )
        db.session.add(user_skill)
        
        # Create organization
        org = Organization(name='Test Org', sector='Information Technology')
        db.session.add(org)
        db.session.flush()
        
        # Create opportunity
        opp = Opportunity(
            organization_id=org.id,
            title='Python Developer',
            description='Python development role',
            skills_required='["Python", "SQL"]',
            location='Bangalore',
            domain='Web Development',
            role_type='Backend Developer',
            is_published=True,
            is_sample=True
        )
        db.session.add(opp)
        
        db.session.commit()
        
        return user.id, opp.id

def test_recommendation_generation(app, setup_data):
    """Test recommendation generation"""
    user_id, opp_id = setup_data
    
    with app.app_context():
        engine = RecommendationEngine()
        rec_id = engine.generate_recommendations(user_id)
        
        assert rec_id is not None
        
        # Check recommendation items were created
        from app.models import RecommendationItem
        items = RecommendationItem.query.filter_by(recommendation_id=rec_id).all()
        assert len(items) > 0
        assert items[0].match_score >= 0
        assert items[0].match_score <= 1

def test_skill_scoring(app, setup_data):
    """Test skill scoring calculation"""
    with app.app_context():
        engine = RecommendationEngine()
        
        # Test perfect match
        score = engine._calculate_skills_score(['Python', 'SQL'], ['Python', 'SQL'])
        assert score == 1.0
        
        # Test partial match
        score = engine._calculate_skills_score(['Python'], ['Python', 'SQL'])
        assert score == 0.5
        
        # Test no match
        score = engine._calculate_skills_score([], ['Python', 'SQL'])
        assert score == 0.0

def test_location_scoring(app, setup_data):
    """Test location scoring calculation"""
    with app.app_context():
        engine = RecommendationEngine()
        
        # Create mock profile
        from app.models import StudentProfile
        profile = StudentProfile(
            preferred_location='Bangalore',
            relocation_preference='yes'
        )
        
        # Test exact match
        score = engine._calculate_location_score(profile, type('obj', (object,), {'location': 'Bangalore'})())
        assert score == 1.0
        
        # Test no match with relocation
        score = engine._calculate_location_score(profile, type('obj', (object,), {'location': 'Delhi'})())
        assert score == 0.8


def test_resume_skills_match_case_insensitively_and_closed_opportunities_are_excluded(app, setup_data):
    user_id, opportunity_id = setup_data
    with app.app_context():
        profile = StudentProfile.query.filter_by(user_id=user_id).one()
        profile.skills = '["sql"]'
        resume = Resume(
            user_id=user_id,
            filename='resume.txt',
            original_filename='resume.txt',
            file_path='',
            source_type='text',
            is_processed=True
        )
        db.session.add(resume)
        db.session.flush()
        db.session.add(ResumeExtraction(
            resume_id=resume.id,
            raw_text='Python and SQL experience',
            extracted_skills='["python", "SQL"]'
        ))

        live_opportunity = db.session.get(Opportunity, opportunity_id)
        live_opportunity.application_deadline = date.today() + timedelta(days=5)
        closed_opportunity = Opportunity(
            organization_id=live_opportunity.organization_id,
            title='Closed Python Internship',
            description='Python and SQL development',
            skills_required='["python", "SQL"]',
            application_deadline=date.today() - timedelta(days=1),
            is_published=True
        )
        db.session.add(closed_opportunity)
        db.session.commit()

        recommendation_id = RecommendationEngine().generate_recommendations(user_id)
        items = RecommendationItem.query.filter_by(
            recommendation_id=recommendation_id
        ).all()
        assert [item.opportunity_id for item in items] == [opportunity_id]
        assert json.loads(items[0].matching_skills) == ['Python', 'SQL']
        assert json.loads(items[0].missing_skills) == []


def test_resume_parser_detects_product_skills_without_partial_word_matches(app):
    with app.app_context():
        parser = ResumeParser()
        skills = parser._extract_skills(
            'Product management, market research, JavaScript, and Python.'
        )
        assert 'Product Management' in skills
        assert 'Market Research' in skills
        assert 'JavaScript' in skills
        assert 'Java' not in skills
