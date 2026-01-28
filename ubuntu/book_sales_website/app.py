"""
Main application file for Book Sales Website

This module initializes the Flask application, configures it,
and includes all the routes for the website functionality.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database models
from database_schema import db, User, Book, Order, OrderItem, Payment, Download
from paypal_helpers import create_payment, execute_payment, get_payment_details
from pdf_helpers import purchase_required, record_download, get_download_path, generate_secure_filename
from admin_helpers import admin_required, get_admin_stats

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///booksales.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['PDF_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/pdfs')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Create database tables
# Flask 2.0+ uses this pattern instead of before_first_request
with app.app_context():
    db.create_all()

# Home route
@app.route('/')
def home():
    """Home page route - displays featured books"""
    books = Book.query.filter_by(is_available=True).limit(6).all()
    return render_template('home.html', books=books)

# Book routes
@app.route('/books')
def book_list():
    """List all available books"""
    books = Book.query.filter_by(is_available=True).all()
    return render_template('books.html', books=books)

@app.route('/books/<int:book_id>')
def book_detail(book_id):
    """Display details for a specific book"""
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

@app.route('/books/search')
def book_search():
    """Search for books by title, author, or description"""
    query = request.args.get('query', '')
    if query:
        # Search in title, author, and description
        search = f"%{query}%"
        books = Book.query.filter(
            (Book.title.ilike(search)) | 
            (Book.author.ilike(search)) | 
            (Book.description.ilike(search))
        ).filter_by(is_available=True).all()
    else:
        books = []
    
    return render_template('search_results.html', books=books, query=query)

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))
        
        # Create new user
        new_user = User(
            email=email,
            password=generate_password_hash(password),
            name=name
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Shopping cart routes
@app.route('/cart')
def cart():
    """Display shopping cart contents"""
    # Get cart from session or initialize empty cart
    cart_items = session.get('cart', {})
    books = []
    total = 0
    
    # Get book details for each item in cart
    for book_id, quantity in cart_items.items():
        book = Book.query.get(int(book_id))
        if book:
            item_total = book.price * quantity
            books.append({
                'book': book,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', items=books, total=total)

@app.route('/cart/add/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    """Add a book to the shopping cart"""
    book = Book.query.get_or_404(book_id)
    
    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = {}
    
    # Add book to cart or increment quantity
    cart = session['cart']
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        cart[book_id_str] += 1
    else:
        cart[book_id_str] = 1
    
    session['cart'] = cart
    flash(f'"{book.title}" added to your cart.', 'success')
    
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:book_id>', methods=['POST'])
def update_cart(book_id):
    """Update quantity of a book in the cart"""
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' in session:
        cart = session['cart']
        book_id_str = str(book_id)
        
        if book_id_str in cart:
            if quantity > 0:
                cart[book_id_str] = quantity
            else:
                # Remove item if quantity is 0
                del cart[book_id_str]
            
            session['cart'] = cart
            flash('Cart updated successfully.', 'success')
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:book_id>', methods=['POST'])
def remove_from_cart(book_id):
    """Remove a book from the cart"""
    if 'cart' in session:
        cart = session['cart']
        book_id_str = str(book_id)
        
        if book_id_str in cart:
            del cart[book_id_str]
            session['cart'] = cart
            flash('Item removed from cart.', 'success')
    
    return redirect(url_for('cart'))

# Checkout and payment routes
@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    """Display checkout page"""
    # Get cart from session
    cart_items = session.get('cart', {})
    
    if not cart_items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('book_list'))
    
    books = []
    total = 0
    
    # Get book details for each item in cart
    for book_id, quantity in cart_items.items():
        book = Book.query.get(int(book_id))
        if book:
            item_total = book.price * quantity
            books.append({
                'book': book,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('checkout.html', items=books, total=total)

@app.route('/create-payment', methods=['POST'])
@login_required
def create_payment_route():
    """Create PayPal payment for checkout"""
    # Get cart from session
    cart_items = session.get('cart', {})
    
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400
    
    # Calculate total amount
    total = 0
    items = []
    
    for book_id, quantity in cart_items.items():
        book = Book.query.get(int(book_id))
        if book:
            item_total = book.price * quantity
            total += item_total
            
            # Add item to PayPal items list
            items.append({
                "name": book.title,
                "sku": f"book-{book.id}",
                "price": str(book.price),
                "currency": "USD",
                "quantity": quantity
            })
    
    # Create PayPal payment using helper function
    return_url = url_for('execute_payment', _external=True)
    cancel_url = url_for('payment_cancelled', _external=True)
    
    result = create_payment(items, total, return_url, cancel_url)
    
    if result["success"]:
        # Store payment ID in session
        session['payment_id'] = result["payment_id"]
        
        # Return approval URL to frontend
        return jsonify({"approval_url": result["approval_url"]})
    else:
        return jsonify({"error": result["error"]}), 400

@app.route('/execute-payment')
@login_required
def execute_payment():
    """Execute PayPal payment after user approval"""
    payment_id = session.get('payment_id')
    payer_id = request.args.get('PayerID')
    
    if not payment_id or not payer_id:
        flash('Payment information missing.', 'danger')
        return redirect(url_for('checkout'))
    
    # Execute payment using helper function
    result = execute_payment(payment_id, payer_id)
    
    if result["success"]:
        # Payment successful, create order in database
        cart_items = session.get('cart', {})
        total_amount = 0
        
        # Create new order
        new_order = Order(
            user_id=current_user.id,
            total_amount=0,  # Will update after calculating items
            status='completed'
        )
        db.session.add(new_order)
        db.session.flush()  # Get order ID without committing
        
        # Add order items
        for book_id, quantity in cart_items.items():
            book = Book.query.get(int(book_id))
            if book:
                item_total = book.price * quantity
                total_amount += item_total
                
                # Create order item
                order_item = OrderItem(
                    order_id=new_order.id,
                    book_id=book.id,
                    quantity=quantity,
                    price=book.price
                )
                db.session.add(order_item)
        
        # Update order total
        new_order.total_amount = total_amount
        
        # Create payment record
        payment_record = Payment(
            order_id=new_order.id,
            amount=total_amount,
            payment_method='paypal',
            transaction_id=payment_id,
            status='completed'
        )
        db.session.add(payment_record)
        
        # Commit all changes
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        session.pop('payment_id', None)
        
        flash('Payment successful! You can now download your books.', 'success')
        return redirect(url_for('order_complete', order_id=new_order.id))
    else:
        flash('Payment execution failed.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/payment-cancelled')
def payment_cancelled():
    """Handle cancelled PayPal payment"""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('checkout'))

@app.route('/order-complete/<int:order_id>')
@login_required
def order_complete(order_id):
    """Display order completion page with download links"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    return render_template('order_complete.html', order=order)

# Download routes
@app.route('/download/<int:book_id>/<int:order_id>')
@login_required
@purchase_required
def download_book(book_id, order_id):
    """Handle secure book download after purchase"""
    # Get the book
    book = Book.query.get_or_404(book_id)
    
    # Record the download
    record_download(
        user_id=current_user.id,
        book_id=book.id,
        order_id=order_id,
        ip_address=request.remote_addr
    )
    
    # Get the file path
    pdf_path = get_download_path(book)
    
    # Send the file
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{book.title}.pdf"
    )

# User account routes
@app.route('/account')
@login_required
def account():
    """Display user account information"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('account.html', user=current_user, orders=orders)

@app.route('/account/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display details for a specific order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_detail.html', order=order)

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard route"""
    books = Book.query.all()
    orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    
    # Get statistics
    stats = get_admin_stats()
    
    return render_template('admin/dashboard.html', 
                          books=books, 
                          orders=orders, 
                          total_books=stats['total_books'],
                          total_users=stats['total_users'],
                          total_orders=stats['total_orders'],
                          total_revenue=stats['total_revenue'])

@app.route('/admin/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_book():
    """Admin route to add a new book"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        language = request.form.get('language')
        pages = request.form.get('pages')
        if pages:
            pages = int(pages)
        
        publication_date = request.form.get('publication_date')
        if publication_date:
            publication_date = datetime.strptime(publication_date, '%Y-%m-%d')
        
        is_available = 'is_available' in request.form
        
        # Handle file uploads
        cover_image = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                cover_image = filename
        
        pdf_file = None
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename:
                filename = generate_secure_filename(file.filename)
                file_path = os.path.join(app.config['PDF_FOLDER'], filename)
                file.save(file_path)
                pdf_file = filename
        
        # Create new book
        new_book = Book(
            title=title,
            author=author,
            description=description,
            price=price,
            isbn=isbn,
            publisher=publisher,
            language=language,
            pages=pages,
            publication_date=publication_date,
            cover_image=cover_image,
            pdf_file=pdf_file,
            is_available=is_available
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_book.html')

@app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_book(book_id):
    """Admin route to edit an existing book"""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        # Update book data
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.price = float(request.form.get('price'))
        book.isbn = request.form.get('isbn')
        book.publisher = request.form.get('publisher')
        book.language = request.form.get('language')
        pages = request.form.get('pages')
        if pages:
            book.pages = int(pages)
        
        publication_date = request.form.get('publication_date')
        if publication_date:
            book.publication_date = datetime.strptime(publication_date, '%Y-%m-%d')
        
        book.is_available = 'is_available' in request.form
        
        # Handle file uploads
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                book.cover_image = filename
        
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename:
                filename = generate_secure_filename(file.filename)
                file_path = os.path.join(app.config['PDF_FOLDER'], filename)
                file.save(file_path)
                book.pdf_file = filename
        
        db.session.commit()
        
        flash('Book updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_book.html', book=book)

@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_book(book_id):
    """Admin route to delete a book"""
    book = Book.query.get_or_404(book_id)
    
    # Delete associated files
    if book.cover_image:
        cover_path = os.path.join(app.config['UPLOAD_FOLDER'], book.cover_image)
        if os.path.exists(cover_path):
            os.remove(cover_path)
    
    if book.pdf_file:
        pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    db.session.delete(book)
    db.session.commit()
    
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/debug/user')
@login_required
def debug_user():
    """Debug route to check current user info"""
    return f"""
    <h1>Current User Debug Info</h1>
    <p>Authenticated: {current_user.is_authenticated}</p>
    <p>User ID: {current_user.id}</p>
    <p>Email: {current_user.email}</p>
    <p>Name: {current_user.name}</p>
    <p>Is Admin: {current_user.is_admin}</p>
    <p>Has is_admin attribute: {hasattr(current_user, 'is_admin')}</p>
    """

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)