from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Application, SavedOpportunity
from datetime import datetime, timezone

applications_bp = Blueprint('applications', __name__)
APPLICATION_STATUSES = {
    'interested', 'preparing', 'applied', 'assessment',
    'selected', 'rejected', 'withdrawn'
}

@applications_bp.route('/')
@login_required
def index():
    """Application tracker"""
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Application.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Order by updated date
    query = query.order_by(Application.updated_at.desc())
    
    # Paginate
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    applications = pagination.items
    
    return render_template('applications/index.html',
                         applications=applications,
                         pagination=pagination,
                         status=status)

@applications_bp.route('/add/<int:opportunity_id>', methods=['GET', 'POST'])
@login_required
def add(opportunity_id):
    """Add application"""
    from app.models.opportunity import Opportunity
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    if request.method == 'POST':
        existing = Application.query.filter_by(
            user_id=current_user.id,
            opportunity_id=opportunity_id
        ).first()
        if existing:
            flash('You are already tracking this opportunity. Update its status here.', 'info')
            return redirect(url_for('applications.edit', application_id=existing.id))

        status = request.form.get('status', 'interested')
        if request.form.get('applied'):
            status = 'applied'
        if status not in APPLICATION_STATUSES:
            flash('Select a valid application status.', 'danger')
            return redirect(url_for('applications.add', opportunity_id=opportunity_id))

        application = Application(
            user_id=current_user.id,
            opportunity_id=opportunity_id,
            status=status,
            application_date=datetime.now(timezone.utc).date() if status == 'applied' else None,
            notes=request.form.get('notes', '')
        )
        
        db.session.add(application)
        db.session.commit()
        
        flash('Application added successfully!', 'success')
        return redirect(url_for('applications.index'))
    
    return render_template('applications/add.html', opportunity=opportunity)

@applications_bp.route('/edit/<int:application_id>', methods=['GET', 'POST'])
@login_required
def edit(application_id):
    """Edit application"""
    application = Application.query.get_or_404(application_id)
    
    # Check ownership
    if application.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('applications.index'))
    
    if request.method == 'POST':
        application.status = request.form.get('status', 'interested')
        application.notes = request.form.get('notes', '')
        
        if request.form.get('application_date'):
            application.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
        
        if request.form.get('follow_up_reminder'):
            application.follow_up_reminder = datetime.strptime(request.form.get('follow_up_reminder'), '%Y-%m-%d').date()
        else:
            application.follow_up_reminder = None
        
        application.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Application updated successfully!', 'success')
        return redirect(url_for('applications.index'))
    
    return render_template('applications/edit.html', application=application)

@applications_bp.route('/delete/<int:application_id>', methods=['POST'])
@login_required
def delete(application_id):
    """Delete application"""
    application = Application.query.get_or_404(application_id)
    
    # Check ownership
    if application.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('applications.index'))
    
    db.session.delete(application)
    db.session.commit()
    
    flash('Application deleted successfully.', 'success')
    return redirect(url_for('applications.index'))
