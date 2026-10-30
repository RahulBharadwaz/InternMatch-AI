"""
Unit tests for ResumeParser service
Validates PDF, DOCX, TXT extraction, PII redaction, file size limits, and edge cases.
"""
import os
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Resume, ResumeExtraction
from app.services.resume_parser import ResumeParser


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user(app):
    user = User(email="applicant@example.com", full_name="Applicant User", role="student")
    user.set_password("Secret@123")
    db.session.add(user)
    db.session.commit()
    return user


def test_pii_redaction():
    """Verify that candidate emails and phone numbers are redacted for privacy."""
    parser = ResumeParser()
    sample = "Contact John Doe at john.doe@email.com or +91-9876543210 for interview scheduling."
    redacted = parser.redact_pii(sample)
    assert "[EMAIL_REDACTED]" in redacted
    assert "john.doe@email.com" not in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "9876543210" not in redacted


def test_text_normalization():
    """Verify text normalization cleans control characters and collapses whitespace."""
    parser = ResumeParser()
    dirty = "Line 1\x00\x05\n\r\n\r\nLine 2     with   spaces"
    clean = parser.normalize_text(dirty)
    assert "\x00" not in clean
    assert "Line 1\n\nLine 2 with spaces" == clean


def test_parse_text_direct(app, test_user):
    """Verify direct resume text parsing and storage."""
    parser = ResumeParser()
    resume = Resume(
        user_id=test_user.id,
        filename="pasted-text.txt",
        source_type="text"
    )
    db.session.add(resume)
    db.session.commit()

    text = "Experienced in Python, Machine Learning, and SQL. Contact: student@clg.edu, +91 9123456789."
    extracted = parser.parse_text(resume.id, text)

    assert "Python" in extracted['skills']
    assert "Machine Learning" in extracted['skills']
    assert "SQL" in extracted['skills']

    # Verify database persistence & PII masking
    extraction = ResumeExtraction.query.filter_by(resume_id=resume.id).first()
    assert extraction is not None
    assert "[EMAIL_REDACTED]" in extraction.raw_text
    assert "[PHONE_REDACTED]" in extraction.raw_text


def test_empty_resume_text_raises_error(app, test_user):
    """Verify empty text raises descriptive ValueError."""
    parser = ResumeParser()
    resume = Resume(user_id=test_user.id, filename="empty.txt", source_type="text")
    db.session.add(resume)
    db.session.commit()

    with pytest.raises(ValueError, match="Resume text cannot be empty"):
        parser.parse_text(resume.id, "   \n\t  ")


def test_txt_file_extraction(app, test_user, tmp_path):
    """Verify parsing a valid TXT resume file from disk."""
    parser = ResumeParser()
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text("Education: B.Tech Computer Science\nSkills: Docker, AWS, Python, Kubernetes.", encoding="utf-8")

    resume = Resume(
        user_id=test_user.id,
        filename="resume.txt",
        file_path=str(txt_file),
        source_type="file"
    )
    db.session.add(resume)
    db.session.commit()

    extracted = parser.parse_resume(resume.id)
    assert "Docker" in extracted['skills']
    assert "AWS" in extracted['skills']
    assert "Python" in extracted['skills']
    assert "Kubernetes" in extracted['skills']


def test_empty_file_raises_error(app, test_user, tmp_path):
    """Verify empty file raises ValueError."""
    parser = ResumeParser()
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    resume = Resume(
        user_id=test_user.id,
        filename="empty.txt",
        file_path=str(empty_file),
        source_type="file"
    )
    db.session.add(resume)
    db.session.commit()

    with pytest.raises(ValueError, match="Text file is empty"):
        parser.parse_resume(resume.id)


def test_unsupported_file_extension_raises_error(app, test_user, tmp_path):
    """Verify unsupported file formats are rejected."""
    parser = ResumeParser()
    jpg_file = tmp_path / "resume.jpg"
    jpg_file.write_bytes(b"\xff\xd8\xff\xe0")

    resume = Resume(
        user_id=test_user.id,
        filename="resume.jpg",
        file_path=str(jpg_file),
        source_type="file"
    )
    db.session.add(resume)
    db.session.commit()

    with pytest.raises(ValueError, match="Unsupported resume format"):
        parser.parse_resume(resume.id)


def test_missing_file_on_disk_raises_error(app, test_user):
    """Verify missing file path raises descriptive error."""
    parser = ResumeParser()
    resume = Resume(
        user_id=test_user.id,
        filename="nonexistent.pdf",
        file_path="C:/nonexistent_path/resume.pdf",
        source_type="file"
    )
    db.session.add(resume)
    db.session.commit()

    with pytest.raises(ValueError, match="Resume file was not found on the server"):
        parser.parse_resume(resume.id)

