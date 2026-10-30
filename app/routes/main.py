from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About InternMatch platform"""
    return render_template('about.html')

@main_bp.route('/how-it-works')
def how_it_works():
    """How It Works page"""
    return render_template('how_it_works.html')

@main_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard"""
    from app.models import StudentProfile, Application, SavedOpportunity, Notification
    from app.models.opportunity import Opportunity
    
    # Get user profile
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get statistics
    applications_count = Application.query.filter_by(user_id=current_user.id).count()
    saved_count = SavedOpportunity.query.filter_by(user_id=current_user.id).count()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # Get recent applications
    recent_applications = Application.query.filter_by(user_id=current_user.id)\
        .order_by(Application.created_at.desc()).limit(5).all()
    
    # Get unread notifications
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html',
                         profile=profile,
                         applications_count=applications_count,
                         saved_count=saved_count,
                         unread_notifications=unread_notifications,
                         recent_applications=recent_applications,
                         notifications=notifications)
