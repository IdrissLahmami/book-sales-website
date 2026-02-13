#!/usr/bin/env python3
"""
Test the admin dashboard book loading specifically
"""

from app import app
from database_schema import Book

def test_dashboard_books():
    """Test how books are loaded in admin dashboard"""
    with app.app_context():
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