from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.opportunity import Opportunity
from app.models import SavedOpportunity

opportunities_bp = Blueprint('opportunities', __name__)

@opportunities_bp.route('/explore')
def explore():
    """Send students to personalized, resume-informed recommendations."""
    if not current_user.is_authenticated:
        return render_template('opportunities/explore.html')
    return redirect(url_for('recommendations.index'))

@opportunities_bp.route('/<int:opportunity_id>')
def detail(opportunity_id):
    """Opportunity details"""
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if saved by current user
    is_saved = False
    if current_user.is_authenticated:
        is_saved = SavedOpportunity.query.filter_by(
            user_id=current_user.id,
            opportunity_id=opportunity_id
        ).first() is not None
    
    return render_template('opportunities/detail.html', opportunity=opportunity, is_saved=is_saved)

@opportunities_bp.route('/save/<int:opportunity_id>', methods=['POST'])
@login_required
def save(opportunity_id):
    """Save opportunity"""
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if already saved
    existing = SavedOpportunity.query.filter_by(
        user_id=current_user.id,
        opportunity_id=opportunity_id
    ).first()
    
    if existing:
        flash('Opportunity already saved.', 'info')
        return redirect(url_for('opportunities.detail', opportunity_id=opportunity_id))
    
    # Save opportunity
    saved = SavedOpportunity(
        user_id=current_user.id,
        opportunity_id=opportunity_id
    )
    
    db.session.add(saved)
    db.session.commit()
    
    flash('Opportunity saved to your list.', 'success')
    return redirect(url_for('opportunities.detail', opportunity_id=opportunity_id))

@opportunities_bp.route('/unsave/<int:opportunity_id>', methods=['POST'])
@login_required
def unsave(opportunity_id):
    """Unsave opportunity"""
    saved = SavedOpportunity.query.filter_by(
        user_id=current_user.id,
        opportunity_id=opportunity_id
    ).first()
    
    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash('Opportunity removed from your list.', 'success')
    
    return redirect(url_for('opportunities.detail', opportunity_id=opportunity_id))
