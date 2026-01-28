"""
Create Sample Book Data Script

This script creates a sample book in the database for testing purposes.
"""

import os
import sys
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models
from database_schema import db, Book
from app import app

def create_sample_book():
    """Create a sample book in the database"""
    with app.app_context():
        # Check if book already exists
        existing_book = Book.query.filter_by(title='Sample Book - RESTful Web APIs').first()
        
        if existing_book:
            print(f"Sample book already exists: {existing_book.title}")
            return
        
        # Create new sample book
        sample_book = Book(
            title='Sample Book - RESTful Web APIs',
            author='Leonard Richardson, Mike Amundsen',
            description='A comprehensive guide to designing and building RESTful web APIs. This book covers best practices, common patterns, and real-world examples.',
            price=29.99,
            cover_image='https://via.placeholder.com/300x450?text=RESTful+Web+APIs',
            pdf_file='sample_restful_apis.pdf',
            isbn='978-1449358068',
            publication_date=datetime(2013, 9, 20).date(),
            publisher="O'Reilly Media",
            created_at=datetime.now(),
            is_available=True
        )
        
        db.session.add(sample_book)
        db.session.commit()
        
        print(f"✓ Sample book created successfully!")
        print(f"Title: {sample_book.title}")
        print(f"Author: {sample_book.author}")
        print(f"Price: ${sample_book.price}")
        print(f"ID: {sample_book.id}")

if __name__ == '__main__':
    create_sample_book()
