from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Opportunity, Organization
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.filter_by(role='student').count()
    total_opportunities = Opportunity.query.count()
    published_opportunities = Opportunity.query.filter_by(is_published=True).count()
    sample_opportunities = Opportunity.query.filter_by(is_sample=True).count()
    
    # Recent users
    recent_users = User.query.filter_by(role='student')\
        .order_by(User.created_at.desc()).limit(10).all()
    
    # Recent opportunities
    recent_opportunities = Opportunity.query\
        .order_by(Opportunity.created_at.desc()).limit(10).all()
    
    return render_template('admin/index.html',
                         total_users=total_users,
                         total_opportunities=total_opportunities,
                         published_opportunities=published_opportunities,
                         sample_opportunities=sample_opportunities,
                         recent_users=recent_users,
                         recent_opportunities=recent_opportunities)

@admin_bp.route('/opportunities')
@login_required
@admin_required
def opportunities():
    """Manage opportunities"""
    page = request.args.get('page', 1, type=int)
    
    query = Opportunity.query.order_by(Opportunity.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    opportunities = pagination.items
    
    return render_template('admin/opportunities.html',
                         opportunities=opportunities,
                         pagination=pagination)

@admin_bp.route('/opportunity/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_opportunity():
    """Add opportunity"""
    if request.method == 'POST':
        from app.models.opportunity import Organization
        import json
        
        # Get or create organization
        org_name = request.form.get('organization', '')
        organization = Organization.query.filter_by(name=org_name).first()
        
        if not organization:
            organization = Organization(
                name=org_name,
                sector=request.form.get('sector', ''),
                is_verified=False
            )
            db.session.add(organization)
            db.session.flush()
        
        # Create opportunity
        opportunity = Opportunity(
            organization_id=organization.id,
            title=request.form.get('title', ''),
            description=request.form.get('description', ''),
            qualification_required=request.form.get('qualification_required', ''),
            minimum_percentage=request.form.get('minimum_percentage', ''),
            skills_required=json.dumps(request.form.getlist('skills')),
            location=request.form.get('location', ''),
            domain=request.form.get('domain', ''),
            role_type=request.form.get('role_type', ''),
            stipend=request.form.get('stipend', ''),
            duration=request.form.get('duration', ''),
            is_published=True,
            is_sample=False,
            source_url=request.form.get('source_url', '')
        )
        
        db.session.add(opportunity)
        db.session.commit()
        
        flash('Opportunity added successfully!', 'success')
        return redirect(url_for('admin.opportunities'))
    
    return render_template('admin/add_opportunity.html')

@admin_bp.route('/opportunity/<int:opportunity_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_opportunity(opportunity_id):
    """Toggle opportunity publication status"""
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    opportunity.is_published = not opportunity.is_published
    db.session.commit()
    
    flash(f'Opportunity {"published" if opportunity.is_published else "unpublished"} successfully.', 'success')
    return redirect(url_for('admin.opportunities'))

@admin_bp.route('/opportunity/<int:opportunity_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_opportunity(opportunity_id):
    """Delete opportunity"""
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    db.session.delete(opportunity)
    db.session.commit()
    
    flash('Opportunity deleted successfully.', 'success')
    return redirect(url_for('admin.opportunities'))
