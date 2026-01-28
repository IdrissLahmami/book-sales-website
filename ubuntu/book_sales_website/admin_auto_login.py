"""
Auto-login route for admin access to Book Sales Website

This adds a special route that automatically logs in as admin.
"""

import os
import sys
from flask import Flask, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import generate_password_hash

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models
from database_schema import db, User
from app import app

@app.route('/admin/auto-login/<token>')
def admin_auto_login(token):
    """Auto-login as admin with a special token"""
    # Simple security token - in production, use a more secure method
    if token != "secure-admin-token-2025":
        flash('Invalid access token.', 'danger')
        return redirect(url_for('home'))
    
    # Find admin user or create if doesn't exist
    admin_email = 'admin@example.com'
    
    with app.app_context():
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            # Create admin user if doesn't exist
            admin_user = User(
                email=admin_email,
                password=generate_password_hash('admin123'),
                name='Admin User',
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
        
        # Ensure user has admin privileges
        if not admin_user.is_admin:
            admin_user.is_admin = True
            db.session.commit()
        
        # Log in as admin
        login_user(admin_user)
        flash('You have been automatically logged in as admin.', 'success')
        
        return redirect(url_for('admin_dashboard'))

# Add this route to the app
if __name__ == "__main__":
    print("Auto-login route added to app.")
    print("Access the admin dashboard with:")
    print("http://your-domain/admin/auto-login/secure-admin-token-2025")
