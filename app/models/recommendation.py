from datetime import datetime, timezone
from app.extensions import db

class Recommendation(db.Model):
    """Recommendation run results"""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    algorithm_version = db.Column(db.String(50), nullable=False)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Profile snapshot
    profile_snapshot = db.Column(db.Text)  # JSON snapshot of profile at generation time
    
    # Relationships
    user = db.relationship('User', backref='recommendations')
    items = db.relationship('RecommendationItem', backref='recommendation', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Recommendation {self.id}>'

class RecommendationItem(db.Model):
    """Individual recommended opportunities"""
    __tablename__ = 'recommendation_items'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendations.id'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    
    # Scores
    match_score = db.Column(db.Float, nullable=False)
    skills_score = db.Column(db.Float)
    education_score = db.Column(db.Float)
    text_similarity_score = db.Column(db.Float)
    semantic_score = db.Column(db.Float, default=0.0)
    preference_score = db.Column(db.Float)
    location_score = db.Column(db.Float)
    
    # Eligibility
    eligibility_status = db.Column(db.String(50))  # eligible, ineligible, insufficient_info, requires_verification
    
    # Explanation
    explanation = db.Column(db.Text)
    matching_skills = db.Column(db.Text)  # JSON array
    missing_skills = db.Column(db.Text)  # JSON array
    
    rank = db.Column(db.Integer)
    
    # Relationships
    opportunity = db.relationship('Opportunity', backref='recommendation_items')
    
    def __repr__(self):
        return f'<RecommendationItem {self.id}>'

class RecommendationFeedback(db.Model):
    """User feedback on recommendations"""
    __tablename__ = 'recommendation_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    
    is_relevant = db.Column(db.Boolean, nullable=False)
    feedback_comment = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='feedback')
    opportunity = db.relationship('Opportunity', backref='feedback')
    
    def __repr__(self):
        return f'<RecommendationFeedback {self.id}>'
