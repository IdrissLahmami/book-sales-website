"""
Admin Password Reset Script for Book Sales Website

This script resets the admin password or creates a new admin user if one doesn't exist.
"""

import os
import sys
from werkzeug.security import generate_password_hash
from flask import Flask
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import database models
from database_schema import db, User

# Create a minimal Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def reset_admin_password():
    """Reset admin password or create a new admin user"""
    with app.app_context():
        # Check if admin user exists
        admin_email = 'admin@example.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        
        new_password = 'admin123'
        hashed_password = generate_password_hash(new_password)
        
        if admin_user:
            print(f"Resetting password for existing admin user: {admin_email}")
            admin_user.password = hashed_password
            db.session.commit()
            print(f"Admin password reset successfully to: {new_password}")
        else:
            print(f"Creating new admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                password=hashed_password,
                name='Admin User',
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"New admin user created with password: {new_password}")
        
        # Verify the user was created/updated correctly
        admin_user = User.query.filter_by(email=admin_email).first()
        if admin_user and admin_user.is_admin:
            print("Admin user verified successfully!")
            print(f"Email: {admin_user.email}")
            print(f"Name: {admin_user.name}")
            print(f"Admin status: {'Yes' if admin_user.is_admin else 'No'}")
        else:
            print("Error: Admin user verification failed!")

if __name__ == '__main__':
    reset_admin_password()
    print("\nYou can now log in with:")
    print("Email: admin@example.com")
    print("Password: admin123")
