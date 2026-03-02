from app import app
from database_schema import db, Book
with app.app_context():
    b = Book.query.filter_by(is_available=True).first()
    if b:
        print(b.id)
    else:
        print('NO_BOOK')
