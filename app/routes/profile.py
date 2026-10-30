from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import StudentProfile, EducationRecord
from datetime import datetime
import json

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    """Profile overview"""
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    education = EducationRecord.query.filter_by(profile_id=profile.id).all() if profile else []
    
    return render_template('profile/index.html', profile=profile, education=education)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit profile"""
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        if profile is None:
            profile = StudentProfile(user_id=current_user.id, completion_percentage=0)
            db.session.add(profile)

        # Personal details
        profile.phone_number = request.form.get('phone_number', '')
        
        # Date of birth
        dob_str = request.form.get('date_of_birth', '')
        if dob_str:
            profile.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        profile.gender = request.form.get('gender', '')
        profile.state = request.form.get('state', '')
        profile.district = request.form.get('district', '')
        profile.city = request.form.get('city', '')
        profile.preferred_language = request.form.get('preferred_language', 'en')
        
        # Employment details
        profile.employment_status = request.form.get('employment_status', '')
        profile.years_of_experience = int(request.form.get('years_of_experience', 0)) if request.form.get('years_of_experience') else 0
        profile.current_employer = request.form.get('current_employer', '')
        profile.current_designation = request.form.get('current_designation', '')
        profile.expected_salary = request.form.get('expected_salary', '')
        
        # Preferences
        preferred_industries = request.form.getlist('preferred_industries')
        preferred_domains = request.form.getlist('preferred_domains')
        preferred_roles = request.form.getlist('preferred_roles')
        skills = request.form.getlist('skills')
        
        profile.preferred_industries = json.dumps(preferred_industries)
        profile.preferred_domains = json.dumps(preferred_domains)
        profile.preferred_roles = json.dumps(preferred_roles)
        profile.skills = json.dumps(skills)
        
        profile.preferred_location = request.form.get('preferred_location', '')
        profile.relocation_preference = request.form.get('relocation_preference', 'no')
        
        # Calculate completion percentage
        completion = 0
        if profile.phone_number: completion += 10
        if profile.state: completion += 10
        if profile.district: completion += 10
        if profile.preferred_industries: completion += 15
        if profile.preferred_domains: completion += 15
        if profile.preferred_roles: completion += 15
        if profile.skills: completion += 15
        if profile.preferred_location: completion += 10
        if EducationRecord.query.filter_by(profile_id=profile.id).first(): completion += 15
        
        profile.completion_percentage = completion
        
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('profile/edit.html', profile=profile)

@profile_bp.route('/education/add', methods=['GET', 'POST'])
@login_required
def add_education():
    """Add education record"""
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        education = EducationRecord(
            profile_id=profile.id,
            highest_qualification=request.form.get('highest_qualification', ''),
            course=request.form.get('course', ''),
            specialization=request.form.get('specialization', ''),
            institution=request.form.get('institution', ''),
            graduation_year=int(request.form.get('graduation_year', 0)) if request.form.get('graduation_year') else None,
            current_status=request.form.get('current_status', ''),
            percentage_cgpa=request.form.get('percentage_cgpa', '')
        )
        
        db.session.add(education)
        
        # Update profile completion
        profile.completion_percentage = min(profile.completion_percentage + 15, 100)
        
        db.session.commit()
        
        flash('Education record added successfully!', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('profile/add_education.html')
