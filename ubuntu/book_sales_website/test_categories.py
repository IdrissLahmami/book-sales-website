#!/usr/bin/env python3
"""
Test script to verify category field is working correctly in the database
"""

import os
import pytest

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'test_misc.db')
os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
os.environ.setdefault('SQLALCHEMY_DATABASE_URI', f"sqlite:///{TEST_DB_PATH}")

from app import app, db
from database_schema import Book

pytestmark = [pytest.mark.db, pytest.mark.integration]


def _seed_book_if_needed():
    if Book.query.count() == 0:
        db.session.add(
            Book(
                title='Category Test Book',
                author='Test Author',
                description='Seed data for category tests',
                price=1.0,
                category='programming',
                pdf_file='category_test.pdf',
                is_available=True,
            )
        )
        db.session.commit()

def test_categories():
    """Test category field functionality"""
    with app.app_context():
        db.create_all()
        _seed_book_if_needed()

        print("=== Book Categories Test ===")
        
        # Get all books and show their categories
        books = Book.query.all()
        print(f"\nFound {len(books)} books in database:")
        
        for book in books:
            category = getattr(book, 'category', 'NO_CATEGORY_FIELD')
            print(f"ID: {book.id} | Title: {book.title[:30]}... | Category: {category}")
        
        # Test if we can update a category
        if books:
            test_book = books[0]
            old_category = getattr(test_book, 'category', None)
            print(f"\n=== Testing Category Update ===")
            print(f"Book: {test_book.title}")
            print(f"Current category: {old_category}")
            
            # Update to test_automation
            test_book.category = 'test_automation'
            db.session.commit()
            
            # Verify the update
            updated_book = db.session.get(Book, test_book.id)
            new_category = getattr(updated_book, 'category', None)
            print(f"Updated category: {new_category}")
            
            # Restore original category
            test_book.category = old_category or 'programming'
            db.session.commit()
            print(f"Restored to: {test_book.category}")
            
        print("\n=== Category Field Test Complete ===")

if __name__ == "__main__":
    test_categories()