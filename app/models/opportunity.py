from datetime import datetime
from app.extensions import db

class Organization(db.Model):
    """Organizations offering internships"""
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    sector = db.Column(db.String(100))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    opportunities = db.relationship('Opportunity', backref='organization', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class Opportunity(db.Model):
    """Internship opportunities"""
    __tablename__ = 'opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    
    # Requirements
    qualification_required = db.Column(db.String(100))
    minimum_percentage = db.Column(db.String(10))
    skills_required = db.Column(db.Text)  # JSON array
    experience_required = db.Column(db.String(50))
    
    # Details
    location = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    role_type = db.Column(db.String(50))
    stipend = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    
    # Dates
    application_deadline = db.Column(db.Date)
    start_date = db.Column(db.Date)
    
    # Status
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    is_sample = db.Column(db.Boolean, default=False, nullable=False)  # Mark as demo data
    
    # Source and verification
    source_url = db.Column(db.String(500))
    verification_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    opportunity_skills = db.relationship('OpportunitySkill', backref='opportunity', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedOpportunity', backref='opportunity', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='opportunity', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Opportunity {self.title}>'

class OpportunitySkill(db.Model):
    """Skills required for opportunities"""
    __tablename__ = 'opportunity_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    skill = db.relationship('Skill', backref='opportunity_skills')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('opportunity_id', 'skill_id', name='unique_opportunity_skill'),)
    
    def __repr__(self):
        return f'<OpportunitySkill {self.opportunity_id}-{self.skill_id}>'
