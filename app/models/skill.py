from datetime import datetime
from app.extensions import db

class Skill(db.Model):
    """Master skill list"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))  # technical, soft, domain
    synonyms = db.Column(db.Text)  # JSON array of synonyms
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class StudentSkill(db.Model):
    """Student skills with proficiency"""
    __tablename__ = 'student_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level = db.Column(db.String(20))  # beginner, intermediate, advanced, expert
    source = db.Column(db.String(50), default='manual')  # manual, resume_extracted
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='student_skills')
    skill = db.relationship('Skill', backref='student_skills')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'skill_id', name='unique_user_skill'),)
    
    def __repr__(self):
        return f'<StudentSkill {self.user_id}-{self.skill_id}>'
