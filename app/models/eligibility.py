from datetime import datetime
from app.extensions import db

class EligibilityRule(db.Model):
    """Eligibility rules for opportunities"""
    __tablename__ = 'eligibility_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    rule_type = db.Column(db.String(50), nullable=False)  # qualification, age, percentage, etc.
    condition = db.Column(db.Text, nullable=False)  # JSON condition logic
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    source = db.Column(db.String(255))
    verification_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<EligibilityRule {self.name}>'
