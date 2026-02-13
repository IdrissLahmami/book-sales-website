#!/usr/bin/env python3
"""
Verify Books 5 and 6 metadata
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database_schema import Book

def verify_books():
    """Verify the metadata for Books 5 and 6"""
    with app.app_context():
        books = Book.query.filter(Book.id.in_([5, 6])).all()
        
        print("📚 Sahih al-Bukhari Volumes Metadata Verification:")
        print("=" * 60)
        
        for book in sorted(books, key=lambda x: x.id):
            print(f"📖 Book ID {book.id}:")
            print(f"   Title: {book.title}")
            print(f"   Author: {book.author}")
            print(f"   Category: {book.category}")
            print(f"   Price: ${book.price}")
            print()
            
        # Check if both are consistently categorized as Islamic books
        islamic_books = [book for book in books if book.category == 'islamic']
        programming_books = [book for book in books if book.category == 'programming']
        
        print("🔍 Category Analysis:")
        print(f"   Islamic category: {len(islamic_books)} books")
        print(f"   Programming category: {len(programming_books)} books")
        
        if len(islamic_books) == 2:
            print("✅ Both Sahih al-Bukhari volumes are properly categorized as Islamic!")
        else:
            print("⚠️  Category inconsistency detected!")

if __name__ == "__main__":
    verify_books()