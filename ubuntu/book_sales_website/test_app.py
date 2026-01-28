"""
Test script for Book Sales Website

This script tests the functionality of the Book Sales Website application.
It includes tests for user authentication, book browsing, shopping cart,
payment processing, and PDF downloads.
"""

import os
import sys
import unittest
from flask import session
from app import app, db
from database_schema import User, Book, Order, OrderItem, Payment, Download
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage

class BookSalesWebsiteTestCase(unittest.TestCase):
    """Test case for Book Sales Website"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        # Create test directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
        
        # Create test database
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data for the database"""
        # Create test user
        test_user = User(
            email='test@example.com',
            password=generate_password_hash('password'),
            name='Test User'
        )
        db.session.add(test_user)
        
        # Create test books
        test_book1 = Book(
            title='Test Book 1',
            author='Test Author 1',
            description='This is a test book 1',
            price=9.99,
            pdf_file='test_book1.pdf',
            is_available=True
        )
        
        test_book2 = Book(
            title='Test Book 2',
            author='Test Author 2',
            description='This is a test book 2',
            price=14.99,
            pdf_file='test_book2.pdf',
            is_available=True
        )
        
        db.session.add(test_book1)
        db.session.add(test_book2)
        
        # Create test PDF files
        with open(os.path.join(app.config['PDF_FOLDER'], 'test_book1.pdf'), 'w') as f:
            f.write('Test PDF content for book 1')
        
        with open(os.path.join(app.config['PDF_FOLDER'], 'test_book2.pdf'), 'w') as f:
            f.write('Test PDF content for book 2')
        
        db.session.commit()
    
    def _login(self, email='test@example.com', password='password'):
        """Helper method to log in a user"""
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def _logout(self):
        """Helper method to log out a user"""
        return self.client.get('/logout', follow_redirects=True)
    
    def _add_to_cart(self, book_id=1):
        """Helper method to add a book to the cart"""
        return self.client.post(f'/cart/add/{book_id}', follow_redirects=True)
    
    def test_home_page(self):
        """Test home page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Store', response.data)
    
    def test_book_list(self):
        """Test book listing page loads correctly"""
        response = self.client.get('/books')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Book 1', response.data)
        self.assertIn(b'Test Book 2', response.data)
    
    def test_book_detail(self):
        """Test book detail page loads correctly"""
        response = self.client.get('/books/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Book 1', response.data)
        self.assertIn(b'Test Author 1', response.data)
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post('/register', data={
            'name': 'New User',
            'email': 'new@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
        # Check if user was created in database
        with app.app_context():
            user = User.query.filter_by(email='new@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'New User')
    
    def test_user_login_logout(self):
        """Test user login and logout"""
        # Test login
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful', response.data)
        
        # Test logout
        response = self._logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
    
    def test_cart_functionality(self):
        """Test shopping cart functionality"""
        # Login first
        self._login()
        
        # Add book to cart
        response = self._add_to_cart(1)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'added to your cart', response.data)
        
        # Check cart page
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Book 1', response.data)
        self.assertIn(b'9.99', response.data)
        
        # Update quantity
        response = self.client.post('/cart/update/1', data={
            'quantity': '2'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cart updated', response.data)
        
        # Remove from cart
        response = self.client.post('/cart/remove/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Item removed from cart', response.data)
    
    def test_checkout_page(self):
        """Test checkout page requires login and shows cart items"""
        # Try checkout without login
        response = self.client.get('/checkout', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
        
        # Login and add item to cart
        self._login()
        self._add_to_cart(1)
        
        # Check checkout page
        response = self.client.get('/checkout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Book 1', response.data)
        self.assertIn(b'9.99', response.data)
        self.assertIn(b'Proceed to Payment', response.data)
    
    def test_payment_creation(self):
        """Test payment creation API endpoint"""
        # Login and add item to cart
        self._login()
        self._add_to_cart(1)
        
        # Test payment creation
        response = self.client.post('/create-payment')
        self.assertEqual(response.status_code, 400)  # Will fail without PayPal credentials
        
        # Note: Full payment testing would require PayPal sandbox credentials
    
    def test_order_completion_page(self):
        """Test order completion page with mock order"""
        # Login
        self._login()
        
        # Create a test order directly in the database
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            book = Book.query.first()
            
            # Create order
            order = Order(
                user_id=user.id,
                total_amount=book.price,
                status='completed'
            )
            db.session.add(order)
            db.session.flush()
            
            # Add order item
            order_item = OrderItem(
                order_id=order.id,
                book_id=book.id,
                quantity=1,
                price=book.price
            )
            db.session.add(order_item)
            
            # Add payment
            payment = Payment(
                order_id=order.id,
                amount=book.price,
                payment_method='paypal',
                transaction_id='test_transaction',
                status='completed'
            )
            db.session.add(payment)
            db.session.commit()
            
            order_id = order.id
        
        # Test order completion page
        response = self.client.get(f'/order-complete/{order_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank You for Your Purchase', response.data)
        self.assertIn(b'Download PDF', response.data)
    
    def test_download_protection(self):
        """Test that downloads are protected and require purchase"""
        # Login
        self._login()
        
        # Try to download without purchase
        response = self.client.get('/download/1/999', follow_redirects=True)
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        # Create a test order with purchase
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            book = Book.query.first()
            
            # Create order
            order = Order(
                user_id=user.id,
                total_amount=book.price,
                status='completed'
            )
            db.session.add(order)
            db.session.flush()
            
            # Add order item
            order_item = OrderItem(
                order_id=order.id,
                book_id=book.id,
                quantity=1,
                price=book.price
            )
            db.session.add(order_item)
            db.session.commit()
            
            order_id = order.id
        
        # Try to download with valid purchase
        response = self.client.get(f'/download/1/{order_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response.headers['Content-Disposition'])
        
        # Check that download was recorded - using a fresh session
        with app.app_context():
            db.session.expire_all()  # Refresh session
            download_count = Download.query.filter_by(order_id=order_id).count()
            self.assertGreater(download_count, 0)

if __name__ == '__main__':
    unittest.main()
