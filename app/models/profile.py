from datetime import datetime
from app.extensions import db

class StudentProfile(db.Model):
    """Student profile information"""
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Personal Details
    phone_number = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))  # male, female, other, prefer_not_to_say
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    city = db.Column(db.String(100))
    preferred_language = db.Column(db.String(20), default='en')
    
    # Employment Status
    employment_status = db.Column(db.String(50))  # employed, unemployed, student, self_employed
    years_of_experience = db.Column(db.Integer, default=0)
    current_employer = db.Column(db.String(200))
    current_designation = db.Column(db.String(100))
    expected_salary = db.Column(db.String(50))  # monthly/annual range
    
    # Preferences
    preferred_industries = db.Column(db.Text)  # JSON array
    preferred_domains = db.Column(db.Text)  # JSON array
    preferred_roles = db.Column(db.Text)  # JSON array
    skills = db.Column(db.Text)  # JSON array
    preferred_location = db.Column(db.String(100))
    relocation_preference = db.Column(db.String(20), default='no')  # yes, no, maybe
    
    # Profile completion
    completion_percentage = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    education_records = db.relationship('EducationRecord', backref='profile', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudentProfile {self.user_id}>'

class EducationRecord(db.Model):
    """Education records for students"""
    __tablename__ = 'education_records'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    
    highest_qualification = db.Column(db.String(100))
    course = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    institution = db.Column(db.String(200))
    graduation_year = db.Column(db.Integer)
    current_status = db.Column(db.String(50))  # pursuing, completed, gap_year
    percentage_cgpa = db.Column(db.String(10))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<EducationRecord {self.id}>'
