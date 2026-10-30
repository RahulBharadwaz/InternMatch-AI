from datetime import datetime
from app.extensions import db

class LearningResource(db.Model):
    """Learning resources for skill development"""
    __tablename__ = 'learning_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)
    resource_type = db.Column(db.String(50))  # course, tutorial, documentation, video
    provider = db.Column(db.String(100))
    
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    skill = db.relationship('Skill', backref='learning_resources')
    
    def __repr__(self):
        return f'<LearningResource {self.title}>'
