"""
Create John Doe PayPal Test User
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import db, User
from app import app

def create_john_doe_user():
    """Create John Doe PayPal test user in the database"""
    with app.app_context():
        email = 'John.Doe997@personal.example.com'
        password = 'test123'
        name = 'John Doe'
        address = '2211 N First St, San Jose, CA 95131'

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User already exists: {existing_user.email}")
            return

        user = User(
            email=email,
            password=generate_password_hash(password),
            name=name,
            address=address,
            is_admin=False,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"✓ John Doe user created successfully!")
        print(f"Email: {user.email}")
        print(f"Password: {password}")
        print(f"Name: {user.name}")
        print(f"Address: {user.address}")

if __name__ == '__main__':
    create_john_doe_user()
