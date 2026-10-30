from datetime import datetime
from app.extensions import db

class SavedOpportunity(db.Model):
    """Opportunities saved by students"""
    __tablename__ = 'saved_opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'opportunity_id', name='unique_saved_opportunity'),)
    
    def __repr__(self):
        return f'<SavedOpportunity {self.user_id}-{self.opportunity_id}>'

class Application(db.Model):
    """Application tracking"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    
    status = db.Column(db.String(50), default='interested', nullable=False)  # interested, preparing, applied, assessment, selected, rejected, withdrawn
    application_date = db.Column(db.Date)
    
    notes = db.Column(db.Text)
    follow_up_reminder = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Application {self.id}>'
