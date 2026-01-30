"""
Main application file for Book Sales Website

This module initializes the Flask application, configures it,
and includes all the routes for the website functionality.
"""

import os
import logging
logging.basicConfig(level=logging.DEBUG)
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
from paypal_helpers import create_payment, execute_payment as paypal_execute_payment, get_payment_details
from pdf_helpers import purchase_required, record_download, get_download_path, generate_secure_filename, extract_pdf_metadata
from pdf_cleaner import clean_pdf_auto, detect_watermark_pages
from admin_helpers import admin_required, get_admin_stats
from pdf_thumbnail import generate_pdf_thumbnail

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///booksales.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['PDF_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/pdfs')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size
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

# Request logging for debugging
@app.before_request
def log_request():
    """Log all requests for debugging"""
    with open('request_log.txt', 'a') as f:
        f.write(f"{datetime.now()} - {request.method} {request.path} - Auth: {current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else 'N/A'}\n")

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
    invalid_items = []
    
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
        else:
            # Mark invalid items for removal
            invalid_items.append(book_id)
    
    # Remove invalid items from cart
    if invalid_items:
        cart = session.get('cart', {})
        for book_id in invalid_items:
            if book_id in cart:
                del cart[book_id]
        session['cart'] = cart
        flash('Some items in your cart are no longer available and have been removed.', 'warning')
    
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
    import sys
    
    # Write to file for debugging since terminal output isn't working
    with open('debug_payment.txt', 'a') as f:
        f.write(f"\n\n=== EXECUTE PAYMENT CALLED at {datetime.now()} ===\n")
        f.write(f"Request URL: {request.url}\n")
        f.write(f"User authenticated: {current_user.is_authenticated}\n")
    
    try:
        # Get payment ID from both session AND URL parameter
        payment_id = session.get('payment_id')
        payment_id_from_url = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        with open('debug_payment.txt', 'a') as f:
            f.write(f"payment_id from session: {payment_id}\n")
            f.write(f"payment_id from URL: {payment_id_from_url}\n")
            f.write(f"payer_id: {payer_id}\n")
            f.write(f"Session data: {dict(session)}\n")
        
        print(f"DEBUG: payment_id from session: {payment_id}", flush=True)
        print(f"DEBUG: payment_id from URL: {payment_id_from_url}", flush=True)
        print(f"DEBUG: payer_id from request: {payer_id}", flush=True)
        print(f"DEBUG: All session data: {dict(session)}", flush=True)
        sys.stdout.flush()
        
        # Use payment_id from URL if session is empty (common issue with redirects)
        if not payment_id and payment_id_from_url:
            payment_id = payment_id_from_url
            print(f"DEBUG: Using payment_id from URL instead of session", flush=True)
            with open('debug_payment.txt', 'a') as f:
                f.write(f"Using payment_id from URL\n")
        
        if not payment_id or not payer_id:
            print(f"ERROR: Missing payment info - payment_id: {payment_id}, payer_id: {payer_id}", flush=True)
            with open('debug_payment.txt', 'a') as f:
                f.write(f"ERROR: Missing payment info\n")
            flash('Payment information missing.', 'danger')
            return redirect(url_for('checkout'))
        
        # Execute payment using helper function
        print(f"DEBUG: Calling paypal_execute_payment with payment_id={payment_id}, payer_id={payer_id}...", flush=True)
        with open('debug_payment.txt', 'a') as f:
            f.write(f"Calling paypal_execute_payment({payment_id}, {payer_id})\n")
        sys.stdout.flush()
        result = paypal_execute_payment(payment_id, payer_id)
        print(f"DEBUG: Result: {result}", flush=True)
        with open('debug_payment.txt', 'a') as f:
            f.write(f"Result: {result}\n")
        sys.stdout.flush()
        
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
    except Exception as e:
        print(f"ERROR in execute_payment: {str(e)}", flush=True)
        with open('debug_payment.txt', 'a') as f:
            f.write(f"EXCEPTION: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
        import traceback
        import sys
        traceback.print_exc()
        sys.stdout.flush()
        flash(f'Payment processing error: {str(e)}', 'danger')
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

@app.route('/account/update-address', methods=['POST'])
@login_required
def update_address():
    """Update user billing address"""
    current_user.address = request.form.get('address')
    current_user.city = request.form.get('city')
    current_user.state = request.form.get('state')
    current_user.zip_code = request.form.get('zip_code')
    current_user.country = request.form.get('country')
    
    db.session.commit()
    
    flash('Address updated successfully!', 'success')
    return redirect(url_for('account'))

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

@app.route('/admin/extract-pdf-metadata', methods=['POST'])
@login_required
@admin_required
def extract_pdf_metadata_endpoint():
    """AJAX endpoint to extract metadata from uploaded PDF"""
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    file = request.files['pdf_file']
    if not file or not file.filename:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    # Save temporarily to extract metadata
    temp_filename = generate_secure_filename(file.filename)
    temp_path = os.path.join(app.config['PDF_FOLDER'], temp_filename)
    file.save(temp_path)
    
    try:
        # Auto-clean watermark pages
        print("🧹 Checking for watermark pages...")
        clean_result = clean_pdf_auto(temp_path)
        
        if clean_result['removed_count'] > 0:
            print(f"✓ Removed {clean_result['removed_count']} watermark page(s)")
        
        # Extract metadata
        metadata = extract_pdf_metadata(temp_path)
        
        # Return metadata as JSON
        return jsonify({
            'success': True,
            'metadata': {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'description': metadata.get('description', ''),
                'publisher': metadata.get('publisher', ''),
                'isbn': metadata.get('isbn', '') or metadata.get('doi', ''),  # Use DOI if ISBN not found
                'pages': metadata.get('pages', 0),
                'language': metadata.get('language', ''),
                'publication_date': metadata.get('publication_date', ''),
                'filename': temp_filename
            }
        })
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            try:
                import time
                time.sleep(0.1)  # Brief delay to ensure file is closed
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors
        return jsonify({'error': str(e)}), 500

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
        isbn = request.form.get('isbn') or None
        publisher = request.form.get('publisher') or None
        language = request.form.get('language') or None
        pages = request.form.get('pages')
        if pages:
            pages = int(pages)
        else:
            pages = None
        
        publication_date = request.form.get('publication_date')
        if publication_date:
            publication_date = datetime.strptime(publication_date, '%Y-%m-%d')
        else:
            publication_date = None
        
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
                
                # Auto-generate thumbnail from PDF if no cover image provided
                if not cover_image:
                    thumbnail_filename = os.path.splitext(filename)[0] + '_thumb.png'
                    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                    if generate_pdf_thumbnail(file_path, thumbnail_path):
                        cover_image = thumbnail_filename
                        flash('Cover image automatically generated from PDF.', 'info')
                    else:
                        flash('Could not generate thumbnail from PDF. Please upload a cover image.', 'warning')
        
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
        # Check if we should re-extract metadata (when no significant user input)
        should_reextract = request.form.get('reextract_metadata') == 'true'
        
        if should_reextract and book.pdf_file:
            # Re-extract metadata from current PDF
            pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
            if os.path.exists(pdf_path):
                from pdf_helpers import extract_pdf_metadata
                metadata = extract_pdf_metadata(pdf_path)
                
                # Always update with re-extracted metadata (overwrite existing)
                if metadata.get('title'):
                    book.title = metadata.get('title')
                if metadata.get('author'):
                    book.author = metadata.get('author')
                if metadata.get('description'):
                    book.description = metadata.get('description')
                if metadata.get('publisher'):
                    book.publisher = metadata.get('publisher')
                isbn_value = metadata.get('isbn') or metadata.get('doi')
                if isbn_value:
                    book.isbn = isbn_value
                if metadata.get('language'):
                    book.language = metadata.get('language')
                if metadata.get('pages'):
                    book.pages = metadata.get('pages')
                pub_date_str = metadata.get('publication_date')
                if pub_date_str:
                    try:
                        book.publication_date = datetime.strptime(pub_date_str, '%d/%m/%Y')
                    except:
                        try:
                            book.publication_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                        except:
                            pass
                
                # Always regenerate thumbnail from current PDF
                old_cover = book.cover_image
                thumbnail_filename = f"thumb_{os.path.basename(book.pdf_file)}.png"
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                
                if generate_pdf_thumbnail(pdf_path, thumbnail_path):
                    book.cover_image = thumbnail_filename
                    # Remove old thumbnail if different
                    if old_cover and old_cover != thumbnail_filename:
                        old_thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], old_cover)
                        if os.path.exists(old_thumb_path):
                            try:
                                os.remove(old_thumb_path)
                            except:
                                pass
                    flash('Cover thumbnail regenerated from PDF.', 'info')
                
                db.session.commit()
                flash('Metadata re-extracted and book updated successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
        
        # Normal update with user input
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.price = float(request.form.get('price'))
        book.isbn = request.form.get('isbn') or None
        book.publisher = request.form.get('publisher') or None
        book.language = request.form.get('language') or None
        pages = request.form.get('pages')
        if pages:
            book.pages = int(pages)
        else:
            book.pages = None
        
        publication_date = request.form.get('publication_date')
        if publication_date:
            book.publication_date = datetime.strptime(publication_date, '%Y-%m-%d')
        else:
            book.publication_date = None
        
        book.is_available = 'is_available' in request.form
        
        # Handle file uploads
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                book.cover_image = filename
        
        pdf_updated = False
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename:
                filename = generate_secure_filename(file.filename)
                file_path = os.path.join(app.config['PDF_FOLDER'], filename)
                file.save(file_path)
                book.pdf_file = filename
                pdf_updated = True
                
                # Auto-generate thumbnail from new PDF if no cover image was uploaded
                if 'cover_image' not in request.files or not request.files['cover_image'].filename:
                    thumbnail_filename = os.path.splitext(filename)[0] + '_thumb.png'
                    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                    if generate_pdf_thumbnail(file_path, thumbnail_path):
                        book.cover_image = thumbnail_filename
                        flash('Cover image automatically updated from new PDF.', 'info')
        
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
    
    try:
        # Delete associated downloads first (foreign key constraint)
        Download.query.filter_by(book_id=book_id).delete()
        
        # Delete associated order items
        OrderItem.query.filter_by(book_id=book_id).delete()
        
        # Delete associated files
        if book.cover_image:
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], book.cover_image)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        if book.pdf_file:
            pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        
        # Finally delete the book
        db.session.delete(book)
        db.session.commit()
        
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/clean-pdf/<int:book_id>', methods=['POST'])
@login_required
@admin_required
def admin_clean_pdf(book_id):
    """Admin route to manually clean watermark pages from a book's PDF"""
    book = Book.query.get_or_404(book_id)
    
    if not book.pdf_file:
        return jsonify({'error': 'No PDF file for this book'}), 400
    
    pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
    
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF file not found'}), 404
    
    # Store values before any operations
    old_cover_image = book.cover_image
    
    try:
        # Clean the PDF
        clean_result = clean_pdf_auto(pdf_path)
        
        if clean_result['removed_count'] > 0:
            # Update page count
            import fitz
            doc = fitz.open(pdf_path)
            new_page_count = len(doc)
            doc.close()
            
            # Regenerate thumbnail from cleaned PDF
            if old_cover_image:
                # Remove old thumbnail
                old_thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], old_cover_image)
                if os.path.exists(old_thumb_path):
                    try:
                        os.remove(old_thumb_path)
                    except:
                        pass  # Ignore if file is locked
            
            # Generate new thumbnail
            thumbnail_filename = f"thumb_{os.path.basename(book.pdf_file)}.png"
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
            if generate_pdf_thumbnail(pdf_path, thumbnail_path):
                book.cover_image = thumbnail_filename
            
            # Update book in single transaction
            book.pages = new_page_count
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Removed {clean_result["removed_count"]} watermark page(s)',
                'removed_pages': [p+1 for p in clean_result['removed_pages']],
                'new_page_count': new_page_count,
                'thumbnail_updated': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No watermark pages detected',
                'removed_pages': [],
                'new_page_count': book.pages
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/view-pdf/<int:book_id>')
@login_required
@admin_required
def admin_view_pdf(book_id):
    """Admin route to view PDF pages with option to remove individual pages"""
    book = Book.query.get_or_404(book_id)
    
    if not book.pdf_file:
        flash('No PDF file for this book', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
    
    if not os.path.exists(pdf_path):
        flash('PDF file not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Get total pages
    import fitz
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    
    return render_template('admin/view_pdf.html', book=book, total_pages=total_pages)

@app.route('/admin/pdf-page-preview/<int:book_id>/<int:page_num>')
@login_required
@admin_required
def admin_pdf_page_preview(book_id, page_num):
    """Generate and return a preview image of a specific PDF page"""
    from flask import send_file
    import io
    
    book = Book.query.get_or_404(book_id)
    
    if not book.pdf_file:
        abort(404)
    
    pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
    
    if not os.path.exists(pdf_path):
        abort(404)
    
    try:
        import fitz
        from PIL import Image
        
        doc = fitz.open(pdf_path)
        
        # Validate page number (1-indexed)
        if page_num < 1 or page_num > len(doc):
            doc.close()
            abort(404)
        
        # Get page (0-indexed)
        page = doc[page_num - 1]
        
        # Render page to image at 150 DPI
        pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))
        img_data = pix.tobytes("png")
        doc.close()
        
        # Return image
        return send_file(
            io.BytesIO(img_data),
            mimetype='image/png',
            as_attachment=False
        )
    except Exception as e:
        abort(500)

@app.route('/admin/remove-pdf-page/<int:book_id>/<int:page_num>', methods=['POST'])
@login_required
@admin_required
def admin_remove_pdf_page(book_id, page_num):
    """Remove a specific page from a PDF"""
    book = Book.query.get_or_404(book_id)
    
    if not book.pdf_file:
        return jsonify({'error': 'No PDF file for this book'}), 400
    
    pdf_path = os.path.join(app.config['PDF_FOLDER'], book.pdf_file)
    
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF file not found'}), 404
    
    # Store old cover image
    old_cover_image = book.cover_image
    
    try:
        import fitz
        import shutil
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Validate page number (1-indexed)
        if page_num < 1 or page_num > total_pages:
            doc.close()
            return jsonify({'error': f'Invalid page number. PDF has {total_pages} pages'}), 400
        
        # Delete the page (0-indexed)
        doc.delete_pages(page_num - 1)
        
        # Save to temp file then move
        temp_path = pdf_path + '.tmp'
        doc.save(temp_path)
        new_page_count = len(doc)
        doc.close()
        
        # Move temp file to original
        shutil.move(temp_path, pdf_path)
        
        # Regenerate thumbnail from first page
        if old_cover_image:
            old_thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], old_cover_image)
            if os.path.exists(old_thumb_path):
                try:
                    os.remove(old_thumb_path)
                except:
                    pass
        
        # Generate new thumbnail
        thumbnail_filename = f"thumb_{os.path.basename(book.pdf_file)}.png"
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
        if generate_pdf_thumbnail(pdf_path, thumbnail_path):
            book.cover_image = thumbnail_filename
        
        # Update book in database
        book.pages = new_page_count
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Page {page_num} removed successfully',
            'new_page_count': new_page_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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