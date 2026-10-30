"""
Integration and API endpoint tests
Validates HTTP routes, status codes, RBAC authorization, and error handling.
"""
from datetime import date, timedelta
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Organization, Opportunity, StudentProfile


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def student_user(app):
    user = User(email="student.test@example.com", full_name="Student Test", role="student")
    user.set_password("Student@123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_opportunity(app):
    org = Organization(name="Tech Corp", sector="IT")
    db.session.add(org)
    db.session.flush()

    opp = Opportunity(
        organization_id=org.id,
        title="Software Intern",
        description="Software development role",
        location="Bangalore",
        is_published=True
    )
    db.session.add(opp)
    db.session.commit()
    return opp


def test_public_routes(client):
    """Verify public landing pages return 200 OK."""
    assert client.get('/').status_code == 200
    assert client.get('/about').status_code == 200
    assert client.get('/faq').status_code == 200
    assert client.get('/how-it-works').status_code == 200


def test_opportunity_detail_success(client, sample_opportunity):
    """Verify opportunity detail view returns 200 for valid ID."""
    response = client.get(f'/opportunities/{sample_opportunity.id}')
    assert response.status_code == 200
    assert b"Software Intern" in response.data


def test_opportunity_detail_404_on_invalid_id(client):
    """Verify non-existent opportunity ID triggers 404 handler."""
    response = client.get('/opportunities/99999')
    assert response.status_code == 404


def test_admin_route_forbidden_for_students(client, student_user):
    """Verify student role cannot access administrator panel."""
    # Login as student
    client.post('/auth/login', data={'email': student_user.email, 'password': 'Student@123'})
    response = client.get('/admin/', follow_redirects=False)
    # Redirects to home page with flash message
    assert response.status_code == 302


def test_unauthenticated_protected_routes_redirect_to_login(client):
    """Verify protected routes redirect unauthenticated users to login page."""
    assert client.get('/dashboard').status_code == 302
    assert client.get('/profile/').status_code == 302
    assert client.get('/recommendations/').status_code == 302
    assert client.get('/applications/').status_code == 302
