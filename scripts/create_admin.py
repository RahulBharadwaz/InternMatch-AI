"""
Create admin user script
Run this to create an administrator account
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import User

def create_admin():
    """Create an admin user"""
    app = create_app('development')
    
    with app.app_context():
        email = input("Enter admin email: ").strip()
        full_name = input("Enter admin full name: ").strip()
        password = input("Enter admin password: ").strip()
        
        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Error: User with email {email} already exists.")
            return
        
        # Create admin user
        admin = User(
            email=email,
            full_name=full_name,
            role='admin',
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"\nAdmin user created successfully!")
        print(f"Email: {email}")
        print(f"Full Name: {full_name}")
        print(f"Role: admin")

if __name__ == '__main__':
    create_admin()
