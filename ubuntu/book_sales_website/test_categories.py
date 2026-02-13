#!/usr/bin/env python3
"""
Test script to verify category field is working correctly in the database
"""

from app import app, db
from database_schema import Book

def test_categories():
    """Test category field functionality"""
    with app.app_context():
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
            updated_book = Book.query.get(test_book.id)
            new_category = getattr(updated_book, 'category', None)
            print(f"Updated category: {new_category}")
            
            # Restore original category
            test_book.category = old_category or 'programming'
            db.session.commit()
            print(f"Restored to: {test_book.category}")
            
        print("\n=== Category Field Test Complete ===")

if __name__ == "__main__":
    test_categories()