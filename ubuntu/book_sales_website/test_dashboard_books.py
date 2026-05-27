#!/usr/bin/env python3
"""
Test the admin dashboard book loading specifically
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
                title='Dashboard Test Book',
                author='Test Author',
                description='Seed data for dashboard tests',
                price=2.0,
                category='programming',
                pdf_file='dashboard_test.pdf',
                is_available=True,
            )
        )
        db.session.commit()

def test_dashboard_books():
    """Test how books are loaded in admin dashboard"""
    with app.app_context():
        db.create_all()
        _seed_book_if_needed()

        print("=== Admin Dashboard Books Test ===")
        
        # Simulate the same query as admin dashboard
        books = Book.query.all()
        print(f"\nLoaded {len(books)} books for dashboard:")
        
        for book in books:
            print(f"\nBook ID {book.id}: {book.title[:40]}...")
            print(f"  - Has category attribute: {hasattr(book, 'category')}")
            if hasattr(book, 'category'):
                print(f"  - Category value: '{book.category}'")
                print(f"  - Category repr: {repr(book.category)}")
                print(f"  - Is 'programming': {book.category == 'programming'}")
            else:
                print(f"  - NO CATEGORY ATTRIBUTE FOUND!")
            
            # Try to access all attributes
            print(f"  - All attributes: {[attr for attr in dir(book) if not attr.startswith('_')]}")

if __name__ == "__main__":
    test_dashboard_books()