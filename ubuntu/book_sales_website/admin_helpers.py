"""
Admin functionality for Book Sales Website

This module provides decorators and helper functions for admin functionality.
"""

from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user

def admin_required(f):
    """
    Decorator to check if user is an admin before allowing access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def get_admin_stats():
    """
    Get statistics for admin dashboard
    
    Returns:
        dict: Dictionary containing statistics
    """
    from database_schema import User, Book, Order, Payment
    
    total_books = Book.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    
    # Calculate total revenue
    total_revenue = 0
    payments = Payment.query.filter_by(status='completed').all()
    for payment in payments:
        total_revenue += payment.amount
    
    return {
        'total_books': total_books,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue
    }
