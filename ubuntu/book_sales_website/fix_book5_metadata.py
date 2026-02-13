#!/usr/bin/env python3
"""
Fix Book ID 5 metadata manually
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from database_schema import Book

def fix_book5_metadata():
    """Fix the metadata for Book ID 5 with correct information"""
    with app.app_context():
        # Get Book ID 5
        book = Book.query.get(5)
        if not book:
            print("❌ Book ID 5 not found!")
            return
            
        print("📚 Current Book ID 5 information:")
        print(f"   Title: {book.title}")
        print(f"   Author: {book.author}")
        print(f"   Category: {book.category}")
        print()
        
        # Update with correct Sahih al-Bukhari Volume 1 information
        print("🔧 Updating Book ID 5 with correct metadata...")
        book.title = "Kalamullah.Com | Sahih al-Bukhari Vol. 1"
        book.author = "Imam Bukhari"
        book.category = "islamic"
        
        # Commit the changes
        db.session.commit()
        
        print("✅ Book ID 5 metadata updated successfully!")
        print("📚 New Book ID 5 information:")
        print(f"   Title: {book.title}")
        print(f"   Author: {book.author}")
        print(f"   Category: {book.category}")
        print()
        
        # Also show Book ID 6 for comparison
        book6 = Book.query.get(6)
        if book6:
            print("📚 Book ID 6 for comparison:")
            print(f"   Title: {book6.title}")
            print(f"   Author: {book6.author}")
            print(f"   Category: {book6.category}")
            
        print("\n🎉 Both volumes now have consistent metadata!")

if __name__ == "__main__":
    fix_book5_metadata()