"""
Check if specific email exists in users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import db, User
from app import app

def check_user_email():
    """Check if John Doe emails exist in database"""
    with app.app_context():
        # Check if John.Doe998@personal.example.com exists
        user998 = User.query.filter_by(email='John.Doe998@personal.example.com').first()
        
        if user998:
            print("FOUND: John.Doe998@personal.example.com")
            print(f"  Name: {user998.name}")
            print(f"  ID: {user998.id}")
            print(f"  Admin: {user998.is_admin}")
        else:
            print("NOT FOUND: John.Doe998@personal.example.com")
        
        # Also check John.Doe997@personal.example.com
        user997 = User.query.filter_by(email='John.Doe997@personal.example.com').first()
        
        if user997:
            print("\nFOUND: John.Doe997@personal.example.com")
            print(f"  Name: {user997.name}")
            print(f"  ID: {user997.id}")
            print(f"  Admin: {user997.is_admin}")
        else:
            print("\nNOT FOUND: John.Doe997@personal.example.com")
        
        # Show all users for reference
        print(f"\nTotal users in database: {User.query.count()}")
        print("\nAll users:")
        all_users = User.query.all()
        for user in all_users:
            print(f"  - {user.email} ({user.name})")

if __name__ == '__main__':
    check_user_email()