"""
Database initialization script for InternMatch
Creates all required tables for users, profiles, opportunities, recommendations, and audit logs.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_database():
    """Initialize database with all tables"""
    from app import create_app, db
    from app.models import user, profile, skill, resume, opportunity, eligibility, recommendation, application, notification, learning, audit
    
    app = create_app('development')
    
    with app.app_context():
        print("Creating InternMatch database tables...")
        
        # Create all tables
        db.create_all()
        
        print("InternMatch database tables created successfully!")
        print("\nTables created:")
        print("- users")
        print("- student_profiles")
        print("- education_records")
        print("- skills")
        print("- student_skills")
        print("- resumes")
        print("- resume_extractions")
        print("- organizations")
        print("- opportunities")
        print("- opportunity_skills")
        print("- eligibility_rules")
        print("- saved_opportunities")
        print("- recommendations")
        print("- recommendation_items")
        print("- recommendation_feedback")
        print("- applications")
        print("- notifications")
        print("- learning_resources")
        print("- audit_logs")
        
        print("\nNext step: Run `python scripts/seed_demo_data.py` to populate demonstration data.")

if __name__ == '__main__':
    init_database()
