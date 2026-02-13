"""
Database schema for Book Sales Website

This module defines the database models for:
- Users: Customer accounts and authentication
- Books: Book information including title, author, price, etc.
- Orders: Purchase information
- Payments: Payment status and transaction details
- Downloads: Tracking of book downloads after purchase
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for customer accounts and authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Address fields
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Book(db.Model):
    """Book model for storing book information"""
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='programming')  # programming, islamic
    cover_image = db.Column(db.String(255), nullable=True)
    pdf_file = db.Column(db.String(255), nullable=False)  # Path to the PDF file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    
    # Additional book metadata
    isbn = db.Column(db.String(20), nullable=True)
    publisher = db.Column(db.String(100), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    language = db.Column(db.String(50), nullable=True)
    pages = db.Column(db.Integer, nullable=True)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='book', lazy=True)
    
    def __repr__(self):
        return f'<Book {self.title}>'

class Order(db.Model):
    """Order model for tracking purchases"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    
    # Unique order reference for tracking
    order_reference = db.Column(db.String(50), unique=True, nullable=False, 
                               default=lambda: str(uuid.uuid4())[:8].upper())
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<Order {self.order_reference}>'

class OrderItem(db.Model):
    """OrderItem model for individual books in an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Payment(db.Model):
    """Payment model for tracking payment status and details"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='paypal')
    transaction_id = db.Column(db.String(100), nullable=True)  # PayPal transaction ID
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    
    def __repr__(self):
        return f'<Payment {self.id}>'

class Download(db.Model):
    """Download model for tracking book downloads after purchase"""
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    download_date = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)  # For security tracking
    
    # Relationships
    user = db.relationship('User', backref=db.backref('downloads', lazy=True))
    book = db.relationship('Book', backref=db.backref('downloads', lazy=True))
    order = db.relationship('Order', backref=db.backref('downloads', lazy=True))
    
    def __repr__(self):
        return f'<Download {self.id}>'
