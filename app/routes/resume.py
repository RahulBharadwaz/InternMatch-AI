from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Resume, ResumeExtraction, StudentProfile
from werkzeug.utils import secure_filename
import os
import uuid
import json

resume_bp = Blueprint('resume', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def _analyze_resume(resume, text=None):
    """Extract resume content and add detected skills to the student's profile."""
    from app.services.resume_parser import ResumeParser

    parser = ResumeParser()
    extracted = parser.parse_text(resume.id, text) if text is not None else parser.parse_resume(resume.id)
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if profile is None:
        profile = StudentProfile(user_id=current_user.id, completion_percentage=0)
        db.session.add(profile)

    existing_skills = []
    if profile.skills:
        try:
            existing_skills = json.loads(profile.skills)
            if not isinstance(existing_skills, list):
                existing_skills = []
        except json.JSONDecodeError:
            current_app.logger.warning(
                "Ignoring malformed saved skills for user %s", current_user.id
            )
    profile.skills = json.dumps(list(dict.fromkeys(
        skill for skill in [*existing_skills, *extracted['skills']]
        if isinstance(skill, str) and skill.strip()
    )))
    db.session.commit()


def _generate_recommendations_after_resume_analysis():
    """Build personalized matches immediately after a resume is analyzed."""
    from app.services.recommendation_engine import RecommendationEngine

    try:
        recommendation_id = RecommendationEngine().generate_recommendations(current_user.id)
    except Exception:
        current_app.logger.exception(
            "Recommendation generation failed after resume analysis for user %s",
            current_user.id
        )
        flash(
            'Resume analyzed, but recommendations could not be generated. '
            'Please retry from your recommendations page.',
            'warning'
        )
        return

    if recommendation_id is None:
        flash('Resume analyzed, but there are no open internships to recommend right now.', 'info')
        return

    flash('Resume analyzed and personalized internship matches are ready.', 'success')


@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload or store a resume using different sources."""
    if request.method == 'POST':
        resume_url = request.form.get('resume_url', '').strip()
        resume_text = request.form.get('resume_text', '').strip()
        source_type = request.form.get('resume_source', 'upload')

        if source_type in {'url', 'text'} and not resume_url and not resume_text:
            flash('Please provide a resume URL or paste your resume text.', 'danger')
            return render_template('resume/upload.html')

        if source_type == 'url' and resume_url:
            existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
            if existing_resume:
                if existing_resume.file_path and os.path.exists(existing_resume.file_path):
                    os.remove(existing_resume.file_path)
                db.session.delete(existing_resume)

            resume = Resume(
                user_id=current_user.id,
                filename='resume-link.txt',
                original_filename='resume-link.txt',
                file_path='',
                file_size=0,
                mime_type='text/plain',
                source_type='url',
                source_url=resume_url,
                is_processed=False
            )
            db.session.add(resume)
            db.session.commit()

            flash('Resume link saved. Upload the resume file or paste its text to analyze it.', 'info')
            return redirect(url_for('resume.upload'))

        if source_type == 'text' and resume_text:
            existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
            if existing_resume:
                if existing_resume.file_path and os.path.exists(existing_resume.file_path):
                    os.remove(existing_resume.file_path)
                db.session.delete(existing_resume)

            resume = Resume(
                user_id=current_user.id,
                filename='resume-text.txt',
                original_filename='resume-text.txt',
                file_path='',
                file_size=len(resume_text.encode('utf-8')),
                mime_type='text/plain',
                source_type='text',
                is_processed=False
            )
            db.session.add(resume)
            db.session.commit()

            try:
                _analyze_resume(resume, resume_text)
            except (ImportError, OSError, ValueError) as error:
                current_app.logger.exception("Resume analysis failed for user %s", current_user.id)
                flash(f'Resume was saved, but analysis failed: {error}', 'warning')
                return redirect(url_for('resume.upload'))

            _generate_recommendations_after_resume_analysis()
            return redirect(url_for('recommendations.index'))

        if 'resume' not in request.files:
            flash('No file selected.', 'danger')
            return render_template('resume/upload.html')

        file = request.files['resume']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return render_template('resume/upload.html')

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF, DOCX, or TXT files only.', 'danger')
            return render_template('resume/upload.html')

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            flash('File size exceeds maximum limit of 16MB.', 'danger')
            return render_template('resume/upload.html')

        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

        upload_path = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)

        existing_resume = Resume.query.filter_by(user_id=current_user.id).first()
        if existing_resume:
            if existing_resume.file_path and os.path.exists(existing_resume.file_path):
                os.remove(existing_resume.file_path)
            db.session.delete(existing_resume)

        resume = Resume(
            user_id=current_user.id,
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            source_type='file',
            is_processed=False
        )

        db.session.add(resume)
        db.session.commit()

        try:
            _analyze_resume(resume)
        except (ImportError, OSError, ValueError) as error:
            current_app.logger.exception("Resume analysis failed for user %s", current_user.id)
            flash(f'Resume was saved, but analysis failed: {error}', 'warning')
            return redirect(url_for('resume.upload'))

        _generate_recommendations_after_resume_analysis()
        return redirect(url_for('recommendations.index'))

    resume = Resume.query.filter_by(user_id=current_user.id).first()
    extraction = ResumeExtraction.query.filter_by(resume_id=resume.id).first() if resume else None
    return render_template('resume/upload.html', resume=resume, extraction=extraction)

@resume_bp.route('/delete', methods=['POST'])
@login_required
def delete():
    """Delete resume"""
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    
    if not resume:
        flash('No resume found.', 'danger')
        return redirect(url_for('resume.upload'))
    
    # Delete file if one was uploaded
    if resume.file_path and os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    
    # Delete from database
    db.session.delete(resume)
    db.session.commit()
    
    flash('Resume deleted successfully.', 'success')
    return redirect(url_for('resume.upload'))
