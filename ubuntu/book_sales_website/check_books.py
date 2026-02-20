"""
Check books in the database and their is_available status
"""
from database_schema import db, Book
from app import app

def check_books():
    with app.app_context():
        books = Book.query.all()
        print(f"Total books: {len(books)}")
        for b in books:
            print(f"- {b.title} | Available: {b.is_available}")

if __name__ == '__main__':
    check_books()
