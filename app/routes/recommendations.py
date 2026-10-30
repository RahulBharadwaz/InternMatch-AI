from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Recommendation, RecommendationItem
from datetime import date

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/')
@login_required
def index():
    """View recommendations"""
    # Get latest recommendation for user
    latest_recommendation = Recommendation.query.filter_by(user_id=current_user.id)\
        .order_by(Recommendation.generated_at.desc()).first()
    
    if not latest_recommendation:
        return render_template(
            'recommendations/index.html',
            recommendation=None,
            items=[],
            today=date.today()
        )
    
    # Get recommendation items
    items = RecommendationItem.query.filter_by(recommendation_id=latest_recommendation.id)\
        .order_by(RecommendationItem.rank).all()
    
    return render_template('recommendations/index.html',
                         recommendation=latest_recommendation,
                         items=items,
                         today=date.today())

@recommendations_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate new recommendations"""
    from app.services.recommendation_engine import RecommendationEngine
    
    # Check if profile exists
    from app.models import StudentProfile
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash('Complete your profile before generating recommendations.', 'warning')
        return redirect(url_for('profile.edit'))
    if profile.completion_percentage < 30:
        flash('Your profile is incomplete, so these initial matches may be less accurate.', 'warning')
    
    # Generate recommendations
    engine = RecommendationEngine()
    try:
        recommendation_id = engine.generate_recommendations(current_user.id)
        if recommendation_id is None:
            flash('There are no open opportunities to recommend right now.', 'info')
            return redirect(url_for('opportunities.explore'))
        flash('Recommendations generated successfully!', 'success')
        return redirect(url_for('recommendations.index'))
    except Exception as e:
        current_app.logger.exception("Recommendation generation failed for user %s", current_user.id)
        flash(f'Error generating recommendations: {str(e)}', 'danger')
        return redirect(url_for('recommendations.index'))
