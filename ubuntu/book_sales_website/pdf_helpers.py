"""
PDF Download Functionality Module

This module provides helper functions for secure PDF download management.
"""

import os
import uuid
from flask import send_file, abort, current_app
from flask_login import current_user
from datetime import datetime
from functools import wraps

from database_schema import db, User, Book, Order, OrderItem, Payment, Download

def purchase_required(f):
    """
    Decorator to check if user has purchased the book before allowing download
    """
    @wraps(f)
    def decorated_function(book_id, order_id, *args, **kwargs):
        # Check if the user has purchased this book
        order = Order.query.filter_by(
            id=order_id, 
            user_id=current_user.id, 
            status='completed'
        ).first()
        
        if not order:
            abort(403)  # Forbidden
        
        # Check if the book is in this order
        order_item = OrderItem.query.filter_by(
            order_id=order.id, 
            book_id=book_id
        ).first()
        
        if not order_item:
            abort(403)  # Forbidden
            
        return f(book_id, order_id, *args, **kwargs)
    return decorated_function

def record_download(user_id, book_id, order_id, ip_address):
    """
    Record a book download in the database
    
    Args:
        user_id (int): User ID
        book_id (int): Book ID
        order_id (int): Order ID
        ip_address (str): IP address of the downloader
        
    Returns:
        Download: The created download record
    """
    download = Download(
        user_id=user_id,
        book_id=book_id,
        order_id=order_id,
        download_date=datetime.utcnow(),
        ip_address=ip_address
    )
    
    db.session.add(download)
    db.session.commit()
    
    return download

def get_download_path(book):
    """
    Get the file path for a book's PDF
    
    Args:
        book (Book): Book object
        
    Returns:
        str: Absolute path to the PDF file
    """
    pdf_folder = current_app.config['PDF_FOLDER']
    return os.path.join(pdf_folder, book.pdf_file)

def get_user_downloads(user_id):
    """
    Get all downloads for a user
    
    Args:
        user_id (int): User ID
        
    Returns:
        list: List of Download objects
    """
    return Download.query.filter_by(user_id=user_id).all()

def get_book_download_count(book_id):
    """
    Get the number of times a book has been downloaded
    
    Args:
        book_id (int): Book ID
        
    Returns:
        int: Number of downloads
    """
    return Download.query.filter_by(book_id=book_id).count()

def generate_secure_filename(original_filename):
    """
    Generate a secure filename for storing PDFs
    
    Args:
        original_filename (str): Original filename
        
    Returns:
        str: Secure filename with UUID
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate a UUID
    unique_id = str(uuid.uuid4())
    
    # Create a secure filename
    secure_filename = f"{unique_id}{ext}"
    
    return secure_filename
