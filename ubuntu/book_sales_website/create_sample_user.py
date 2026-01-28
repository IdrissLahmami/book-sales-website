"""
Create Sample User Script

This script creates a sample user for testing the billing address functionality.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models
from database_schema import db, User
from app import app

def create_sample_user():
    """Create a sample user in the database"""
    with app.app_context():
        # Check if user already exists
        test_email = 'testuser@example.com'
        existing_user = User.query.filter_by(email=test_email).first()
        
        if existing_user:
            print(f"Test user already exists: {existing_user.email}")
            return
        
        # Create new sample user
        sample_user = User(
            email=test_email,
            password=generate_password_hash('password123'),
            name='Test User',
            is_admin=False,
            is_active=True
        )
        
        db.session.add(sample_user)
        db.session.commit()
        
        print(f"✓ Sample user created successfully!")
        print(f"Email: {sample_user.email}")
        print(f"Name: {sample_user.name}")
        print(f"Password: password123")
        print(f"ID: {sample_user.id}")

if __name__ == '__main__':
    create_sample_user()
