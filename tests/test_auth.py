"""
Tests for authentication functionality
"""
import pytest
from app import create_app
from app.extensions import db
from app.models import (
    Application, Organization, Opportunity, Resume, ResumeExtraction,
    Recommendation, RecommendationItem, StudentProfile, User
)

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_register(client):
    """Test user registration"""
    response = client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    assert response.status_code == 302  # Redirect after successful registration
    
    # Check user was created
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.full_name == 'Test User'

def test_register_duplicate_email(client):
    """Test registration with duplicate email"""
    # Register first user
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    
    # Try to register with same email
    response = client.post('/auth/register', data={
        'full_name': 'Another User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    assert response.status_code == 200  # Stay on page with error

def test_login(client):
    """Test user login"""
    # Register user first
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    
    # Login
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    assert response.status_code == 302  # Redirect after successful login


def test_login_again_with_different_email_case(client):
    """Email casing should not prevent a registered user from signing in again."""
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })

    first_login = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    assert first_login.status_code == 302

    client.get('/auth/logout')
    second_login = client.post('/auth/login', data={
        'email': 'TEST@EXAMPLE.COM',
        'password': 'Test@123'
    })
    assert second_login.status_code == 302


def test_edit_profile_creates_missing_profile(client, app):
    """Editing should repair accounts that do not yet have a profile row."""
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })

    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        db.session.delete(user.profile)
        db.session.commit()

    response = client.post('/profile/edit', data={
        'phone_number': '1234567890',
        'preferred_language': 'en',
        'years_of_experience': '0',
        'relocation_preference': 'no'
    })

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user.profile is not None
        assert user.profile.phone_number == '1234567890'


def test_pasted_resume_is_analyzed_and_updates_profile_skills(client, app):
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })

    response = client.post('/resume/upload', data={
        'resume_source': 'text',
        'resume_text': 'Product management and Python skills with SQL experience.'
    })

    assert response.status_code == 302
    resume_page = client.get('/resume/upload')
    assert resume_page.status_code == 200
    assert b'Product Management' in resume_page.data
    with app.app_context():
        resume = Resume.query.one()
        extraction = ResumeExtraction.query.filter_by(resume_id=resume.id).one()
        profile = StudentProfile.query.one()
        assert resume.is_processed is True
        assert 'Product Management' in extraction.extracted_skills
        assert 'Python' in profile.skills
        assert 'SQL' in profile.skills


def test_application_tracker_prevents_duplicate_and_tracks_applied_status(client, app):
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    with app.app_context():
        organization = Organization(name='Test Organization')
        db.session.add(organization)
        db.session.flush()
        opportunity = Opportunity(
            organization_id=organization.id,
            title='Test Internship',
            description='A test opportunity',
            is_published=True
        )
        db.session.add(opportunity)
        db.session.commit()
        opportunity_id = opportunity.id

    first_response = client.post(
        f'/applications/add/{opportunity_id}',
        data={'status': 'applied'}
    )
    second_response = client.post(
        f'/applications/add/{opportunity_id}',
        data={'status': 'interested'}
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 302
    assert '/applications/edit/' in second_response.headers['Location']
    with app.app_context():
        application = Application.query.one()
        assert application.status == 'applied'
        assert application.application_date is not None


def test_opportunity_explorer_redirects_to_personalized_recommendations(client):
    response = client.get('/opportunities/explore?status=closed&industry=Technology')

    assert response.status_code == 200
    assert b'Resume' in response.data
    assert b'All Industries' not in response.data
    assert b'InternMatch' in response.data

    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    response = client.get('/opportunities/explore?status=closed&industry=Technology')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/recommendations/')
    recommendations_response = client.get('/recommendations/')
    assert recommendations_response.status_code == 200
    assert b'Recommendations' in recommendations_response.data


def test_new_student_can_generate_initial_recommendations(client, app):
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    with app.app_context():
        organization = Organization(name='Test Organization')
        db.session.add(organization)
        db.session.flush()
        db.session.add(Opportunity(
            organization_id=organization.id,
            title='Starter Internship',
            description='A starter internship opportunity',
            is_published=True
        ))
        db.session.commit()

    dashboard_response = client.get('/dashboard')
    assert dashboard_response.status_code == 200
    assert b'<form action="/recommendations/generate" method="POST">' in dashboard_response.data

    response = client.post('/recommendations/generate')
    recommendations_page = client.get('/recommendations/')

    assert response.status_code == 302
    assert recommendations_page.status_code == 200
    assert b'Starter Internship' in recommendations_page.data
    with app.app_context():
        assert Recommendation.query.count() == 1


def test_analyzing_resume_automatically_generates_personalized_matches(client, app):
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'Test@123',
        'confirm_password': 'Test@123'
    })
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'Test@123'
    })
    with app.app_context():
        organization = Organization(name='Test Organization')
        db.session.add(organization)
        db.session.flush()
        opportunity = Opportunity(
            organization_id=organization.id,
            title='Product and Python Internship',
            description='Support product management projects using Python and SQL.',
            skills_required='["Product Management", "Python", "SQL"]',
            is_published=True
        )
        db.session.add(opportunity)
        db.session.commit()
        opportunity_id = opportunity.id

    response = client.post('/resume/upload', data={
        'resume_source': 'text',
        'resume_text': 'Product management and Python skills with SQL experience.'
    })

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/recommendations/')
    with app.app_context():
        recommendation = Recommendation.query.one()
        item = RecommendationItem.query.filter_by(
            recommendation_id=recommendation.id,
            opportunity_id=opportunity_id
        ).one()
        assert item.match_score > 0


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/auth/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  # Stay on page with error

def test_password_validation(client):
    """Test password validation"""
    response = client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'short',  # Too short
        'confirm_password': 'short'
    })
    assert response.status_code == 200  # Stay on page with error
