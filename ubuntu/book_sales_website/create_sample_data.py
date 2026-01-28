"""
Create sample data for Book Sales Website

This script creates a sample admin user and demo books for testing purposes.
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import Flask
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import database models
from database_schema import db, User, Book

# Create a minimal Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_sample_data():
    """Create sample admin user and demo books"""
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user if it doesn't exist
        admin_email = 'admin@example.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            print(f"Creating admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                password=generate_password_hash('admin123'),
                name='Admin User',
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print(f"Admin user {admin_email} already exists")
        
        # Create sample books if none exist
        if Book.query.count() == 0:
            print("Creating sample books...")
            
            # Sample book data
            sample_books = [
                {
                    'title': 'Python Programming for Beginners',
                    'author': 'John Smith',
                    'description': 'A comprehensive guide to Python programming for absolute beginners. Learn the fundamentals of Python, data structures, and basic algorithms.',
                    'price': 19.99,
                    'isbn': '978-1234567890',
                    'publisher': 'Tech Publishing House',
                    'language': 'English',
                    'pages': 320,
                    'publication_date': datetime(2023, 5, 15),
                    'is_available': True,
                    'pdf_file': 'python_beginners.pdf'
                },
                {
                    'title': 'Advanced Web Development',
                    'author': 'Sarah Johnson',
                    'description': 'Master modern web development techniques including responsive design, JavaScript frameworks, and backend integration.',
                    'price': 24.99,
                    'isbn': '978-0987654321',
                    'publisher': 'Web Dev Press',
                    'language': 'English',
                    'pages': 450,
                    'publication_date': datetime(2023, 8, 10),
                    'is_available': True,
                    'pdf_file': 'advanced_web_dev.pdf'
                },
                {
                    'title': 'Data Science Essentials',
                    'author': 'Michael Chen',
                    'description': 'Learn the core concepts of data science, including data analysis, visualization, and machine learning algorithms.',
                    'price': 29.99,
                    'isbn': '978-5678901234',
                    'publisher': 'Data Insights Publishing',
                    'language': 'English',
                    'pages': 380,
                    'publication_date': datetime(2023, 3, 22),
                    'is_available': True,
                    'pdf_file': 'data_science.pdf'
                },
                {
                    'title': 'Mobile App Development with Flutter',
                    'author': 'Emily Rodriguez',
                    'description': 'A practical guide to building cross-platform mobile applications using Flutter and Dart.',
                    'price': 22.99,
                    'isbn': '978-2345678901',
                    'publisher': 'Mobile Dev Books',
                    'language': 'English',
                    'pages': 290,
                    'publication_date': datetime(2023, 9, 5),
                    'is_available': True,
                    'pdf_file': 'flutter_dev.pdf'
                },
                {
                    'title': 'Cybersecurity Fundamentals',
                    'author': 'David Wilson',
                    'description': 'Understand the principles of cybersecurity, common threats, and how to protect digital assets and information.',
                    'price': 27.99,
                    'isbn': '978-3456789012',
                    'publisher': 'Security Press',
                    'language': 'English',
                    'pages': 410,
                    'publication_date': datetime(2023, 6, 18),
                    'is_available': True,
                    'pdf_file': 'cybersecurity.pdf'
                }
            ]
            
            # Create sample PDF files
            pdf_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/pdfs')
            os.makedirs(pdf_folder, exist_ok=True)
            
            for book_data in sample_books:
                # Create sample PDF file if it doesn't exist
                pdf_path = os.path.join(pdf_folder, book_data['pdf_file'])
                if not os.path.exists(pdf_path):
                    with open(pdf_path, 'w') as f:
                        f.write(f"Sample PDF content for {book_data['title']} by {book_data['author']}\n")
                        f.write("This is a placeholder PDF file for demonstration purposes.\n")
                        f.write(f"ISBN: {book_data['isbn']}\n")
                        f.write(f"Publisher: {book_data['publisher']}\n")
                        f.write(f"Pages: {book_data['pages']}\n")
                        f.write("\nCopyright © 2023. All rights reserved.")
                
                # Create book record
                book = Book(**book_data)
                db.session.add(book)
            
            db.session.commit()
            print(f"Created {len(sample_books)} sample books successfully!")
        else:
            print("Sample books already exist in the database")

if __name__ == '__main__':
    create_sample_data()
    print("Sample data creation completed!")
