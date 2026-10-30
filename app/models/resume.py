from datetime import datetime
from app.extensions import db

class Resume(db.Model):
    """Resume uploads"""
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    filename = db.Column(db.String(255), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    source_type = db.Column(db.String(20), default='file')
    source_url = db.Column(db.String(500))
    
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='resume')
    extraction = db.relationship('ResumeExtraction', backref='resume', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Resume {self.user_id}>'

class ResumeExtraction(db.Model):
    """Extracted data from resumes"""
    __tablename__ = 'resume_extractions'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False, unique=True)
    
    raw_text = db.Column(db.Text)
    extracted_skills = db.Column(db.Text)  # JSON array
    extracted_education = db.Column(db.Text)  # JSON array
    extracted_projects = db.Column(db.Text)  # JSON array
    extracted_certifications = db.Column(db.Text)  # JSON array
    extracted_experience = db.Column(db.Text)  # JSON array
    
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_reviewed = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<ResumeExtraction {self.resume_id}>'
