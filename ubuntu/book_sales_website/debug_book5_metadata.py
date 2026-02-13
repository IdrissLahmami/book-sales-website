#!/usr/bin/env python3
"""
Debug PDF metadata extraction for Book ID 5
"""

from app import app, db
from database_schema import Book
import os
from pdf_helpers import extract_pdf_metadata

def debug_book_metadata():
    """Debug metadata extraction for Book ID 5"""
    with app.app_context():
        print("=== PDF Metadata Debug ===")
        
        # Get Book ID 5 and 6 for comparison
        book5 = Book.query.get(5)
        book6 = Book.query.get(6)
        
        if book5:
            print(f"\n--- Book ID 5 ---")
            print(f"Current Title: '{book5.title}'")
            print(f"PDF File: {book5.pdf_file}")
            print(f"Author: {book5.author}")
            
            # Check if PDF file exists
            pdf_path = os.path.join(app.config['PDF_FOLDER'], book5.pdf_file)
            print(f"PDF Path: {pdf_path}")
            print(f"PDF Exists: {os.path.exists(pdf_path)}")
            
            if os.path.exists(pdf_path):
                print("\n--- Attempting Fresh Metadata Extraction ---")
                try:
                    metadata = extract_pdf_metadata(pdf_path)
                    print(f"Extracted Title: '{metadata.get('title', 'NO_TITLE')}'")
                    print(f"Extracted Author: '{metadata.get('author', 'NO_AUTHOR')}'")
                    print(f"All Metadata: {metadata}")
                except Exception as e:
                    print(f"Error extracting metadata: {e}")
            
        if book6:
            print(f"\n--- Book ID 6 (for comparison) ---")
            print(f"Title: '{book6.title}'")
            print(f"PDF File: {book6.pdf_file}")
            print(f"Author: {book6.author}")

if __name__ == "__main__":
    debug_book_metadata()