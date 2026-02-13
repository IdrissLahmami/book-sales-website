#!/usr/bin/env python3
"""
Migration script to add category field to Book table
"""

from app import app, db
from database_schema import Book

def migrate_add_category():
    """Add category field to existing Book table"""
    with app.app_context():
        # Check if category column already exists
        try:
            # Try to query the category column
            from sqlalchemy import text
            result = db.session.execute(text("SELECT category FROM books LIMIT 1;"))
            print("Category column already exists!")
            return
        except:
            print("Category column does not exist, adding it...")
        
        try:
            # Add the category column with a default value using SQLAlchemy text()
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE books ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'programming';"))
            db.session.commit()
            print("✅ Successfully added category column to books table!")
            
            # Update existing books to have programming category by default
            books = Book.query.all()
            for book in books:
                if not hasattr(book, 'category') or book.category is None:
                    book.category = 'programming'
            
            db.session.commit()
            print(f"✅ Updated {len(books)} existing books with default 'programming' category!")
            
        except Exception as e:
            print(f"❌ Error adding category column: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_add_category()