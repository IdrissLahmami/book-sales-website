"""
Clear Cart Session Script

This script helps clear any corrupted cart data.
"""

import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

with app.app_context():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            if 'cart' in sess:
                print(f"Current cart contents: {sess['cart']}")
                sess['cart'] = {}
                print("Cart cleared!")
            else:
                print("No cart found in session")
    
    # Also check books in database
    from database_schema import Book
    books = Book.query.all()
    print(f"\nBooks in database:")
    for book in books:
        print(f"  ID: {book.id}, Title: {book.title}")
