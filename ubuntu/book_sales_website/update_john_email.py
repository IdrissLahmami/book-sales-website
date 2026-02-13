"""
Update John Doe email from 998 to 997 in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import db, User
from app import app

def update_john_doe_email():
    """Update John Doe email from 998 to 997"""
    with app.app_context():
        # Find the existing user
        old_user = User.query.filter_by(email='John.Doe998@personal.example.com').first()
        
        if old_user:
            print(f"Found user: {old_user.email} ({old_user.name})")
            
            # Check if 997 email already exists
            existing_997 = User.query.filter_by(email='John.Doe997@personal.example.com').first()
            if existing_997:
                print("ERROR: John.Doe997@personal.example.com already exists!")
                return
            
            # Update the email
            old_user.email = 'John.Doe997@personal.example.com'
            
            try:
                db.session.commit()
                print("SUCCESS: Updated email from John.Doe998@personal.example.com to John.Doe997@personal.example.com")
            except Exception as e:
                db.session.rollback()
                print(f"ERROR: Failed to update email - {e}")
        else:
            print("ERROR: John.Doe998@personal.example.com not found in database")
        
        # Show all users after update
        print("\nUsers after update:")
        all_users = User.query.all()
        for user in all_users:
            print(f"  - {user.email} ({user.name})")

if __name__ == '__main__':
    update_john_doe_email()