"""
PDF Download Functionality Module

This module provides helper functions for secure PDF download management
and PDF metadata extraction.
"""

import os
import uuid
import re
from flask import send_file, abort, current_app
from flask_login import current_user
from datetime import datetime
from functools import wraps

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    from langdetect import detect, DetectorFactory
    OCR_AVAILABLE = True
    
    # Configure Tesseract path for Windows
    import platform
    if platform.system() == 'Windows':
        # Common installation paths for Tesseract on Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\Public\Tesseract-OCR\tesseract.exe'
        ]
        tesseract_found = False
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                tesseract_found = True
                print(f"✓ Tesseract found at: {path}")
                break
        if not tesseract_found:
            print("⚠ Tesseract executable not found in common paths")
except ImportError as e:
    OCR_AVAILABLE = False
    print(f"⚠ OCR libraries not available: {e}")

from database_schema import db, User, Book, Order, OrderItem, Payment, Download

def purchase_required(f):
    """
    Decorator to check if user has purchased the book before allowing download.
    Admins can download without purchase.
    """
    @wraps(f)
    def decorated_function(book_id, order_id, *args, **kwargs):
        # Allow admins to download without purchase
        if current_user.is_admin:
            return f(book_id, order_id, *args, **kwargs)
        
        # Check if the user has purchased this book
        order = Order.query.filter_by(
            id=order_id, 
            user_id=current_user.id, 
            status='completed'
        ).first()
        
        if not order:
            abort(403)  # Forbidden
        
        # Check if the book is in this order
        order_item = OrderItem.query.filter_by(
            order_id=order.id, 
            book_id=book_id
        ).first()
        
        if not order_item:
            abort(403)  # Forbidden
            
        return f(book_id, order_id, *args, **kwargs)
    return decorated_function

def record_download(user_id, book_id, order_id, ip_address):
    """
    Record a book download in the database
    
    Args:
        user_id (int): User ID
        book_id (int): Book ID
        order_id (int): Order ID
        ip_address (str): IP address of the downloader
        
    Returns:
        Download: The created download record
    """
    download = Download(
        user_id=user_id,
        book_id=book_id,
        order_id=order_id,
        download_date=datetime.utcnow(),
        ip_address=ip_address
    )
    
    db.session.add(download)
    db.session.commit()
    
    return download

def get_download_path(book):
    """
    Get the file path for a book's PDF
    
    Args:
        book (Book): Book object
        
    Returns:
        str: Absolute path to the PDF file
    """
    pdf_folder = current_app.config['PDF_FOLDER']
    return os.path.join(pdf_folder, book.pdf_file)

def get_user_downloads(user_id):
    """
    Get all downloads for a user
    
    Args:
        user_id (int): User ID
        
    Returns:
        list: List of Download objects
    """
    return Download.query.filter_by(user_id=user_id).all()

def get_book_download_count(book_id):
    """
    Get the number of times a book has been downloaded
    
    Args:
        book_id (int): Book ID
        
    Returns:
        int: Number of downloads
    """
    return Download.query.filter_by(book_id=book_id).count()

def generate_secure_filename(original_filename):
    """
    Generate a secure filename for storing PDFs
    
    Args:
        original_filename (str): Original filename
        
    Returns:
        str: Secure filename with UUID
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate a UUID
    unique_id = str(uuid.uuid4())
    
    # Create a secure filename
    secure_filename = f"{unique_id}{ext}"
    
    return secure_filename

def extract_text_from_cover(pdf_path):
    """
    Extract text from PDF cover using OCR.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from cover
    """
    if not PYMUPDF_AVAILABLE or not OCR_AVAILABLE:
        return ''
    
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return ''
        
        # Get first page
        page = doc[0]
        
        # Render page to image at higher resolution for better OCR
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        
        # Extract text using OCR
        text = pytesseract.image_to_string(img)
        
        doc.close()
        return text
        
    except Exception as e:
        print(f"Error extracting text from cover: {e}")
        return ''

def parse_cover_text(text):
    """
    Parse extracted cover text to find title, author, ISBN, and publisher.
    Note: Description is NOT extracted from cover (too unreliable), use introduction page instead.
    
    Args:
        text (str): OCR extracted text from cover
        
    Returns:
        dict: Parsed metadata
    """
    metadata = {
        'title': '',
        'author': '',
        'publisher': '',
        'isbn': ''
    }
    
    if not text:
        return metadata
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Helper function to check if a line looks like a person's name
    def looks_like_person_name(line):
        words = line.split()
        if not (2 <= len(words) <= 4):
            return False
        if len(line) >= 50:
            return False
        # Each word should start with uppercase and contain only letters
        for word in words:
            if not word or not word[0].isupper():
                return False
            # Check if word contains only letters (no #, numbers, etc)
            if not all(c.isalpha() or c in ['.', ',', '-', "'"] for c in word):
                return False
        # Exclude common non-name words
        non_name_words = ['programming', 'edition', 'volume', 'series', 'guide', 'introduction', 'advanced', 'complete', 'professional', 'press', 'publishing']
        if any(word.lower() in non_name_words for word in words):
            return False
        return True
    
    # ISBN extraction
    isbn_pattern = r'ISBN[:\s-]*([0-9]{13}|[0-9]{10}|[0-9\-]{10,17})'
    for line in lines:
        isbn_match = re.search(isbn_pattern, line, re.IGNORECASE)
        if isbn_match:
            isbn = isbn_match.group(1).replace('-', '').replace(' ', '')
            if len(isbn) in [10, 13]:
                metadata['isbn'] = isbn
                break
    
    # Title extraction - combine first 1-3 lines that aren't author names
    title_lines = []
    author_start_index = 0
    
    for i, line in enumerate(lines[:4]):  # Check first 4 lines max
        # Stop if this looks like an author name
        if looks_like_person_name(line):
            author_start_index = i
            break
        # Add to title if it's short text (likely part of title)
        if len(line) < 50:
            title_lines.append(line)
        else:
            break
    
    if title_lines:
        potential_title = ' '.join(title_lines)
        # Reject if it's just publisher names or very short
        publisher_keywords = ['manning', 'press', 'publishing', 'publisher', 'ebook', 'provided']
        if len(potential_title) > 5 and not any(kw in potential_title.lower() for kw in publisher_keywords):
            metadata['title'] = potential_title
    
    # Author detection (look for common patterns)
    author_keywords = ['by', 'author', 'written by']
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for keyword in author_keywords:
            if keyword in line_lower:
                # Author might be on same line or next line
                author = line.replace(keyword, '').replace(':', '').strip()
                if not author and i + 1 < len(lines):
                    author = lines[i + 1]
                if author:
                    metadata['author'] = author
                    break
        if metadata['author']:
            break
    
    # If no "by" keyword, look for author name(s) in lines after title
    if not metadata['author']:
        # Start looking from where title ended
        authors = []
        for i, line in enumerate(lines[author_start_index:min(author_start_index+5, len(lines))], start=author_start_index):
            if looks_like_person_name(line):
                authors.append(line)
                # Check if next line is also an author
                if i + 1 < len(lines) and looks_like_person_name(lines[i + 1]):
                    continue  # Keep collecting authors
                else:
                    break  # Stop after last author
        
        if authors:
            metadata['author'] = ', '.join(authors)
    
    # Extract publisher from lines after author
    publisher_keywords = ['osborne', 'press', 'publishing', 'books', 'mcgraw', 'wiley', 'oreilly', "o'reilly", 'pearson', 'apress', 'manning', 'packt', 'springer', 'elsevier']
    
    for line in lines:
        line_lower = line.lower()
        for keyword in publisher_keywords:
            if keyword in line_lower:
                # Clean up common OCR errors
                publisher = line.strip()
                publisher = publisher.replace('me OSBORNE', 'McGraw-Hill/Osborne')
                publisher = publisher.replace('OSBORNE', 'McGraw-Hill/Osborne')
                publisher = publisher.replace('me ', '')
                metadata['publisher'] = publisher
                break
        if metadata['publisher']:
            break
    
    return metadata

def extract_pdf_metadata(pdf_path):
    """
    Extract metadata from a PDF file including title, author, ISBN, etc.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing extracted metadata
    """
    metadata = {
        'title': '',
        'author': '',
        'description': '',
        'subject': '',
        'keywords': '',
        'creator': '',
        'producer': '',
        'publisher': '',
        'creation_date': None,
        'publication_date': '',
        'isbn': '',
        'doi': '',
        'pages': 0,
        'language': ''
    }
    
    def detect_language_from_text(text):
        """Detect language from text sample using AI"""
        try:
            # Set seed for consistent results
            DetectorFactory.seed = 0
            
            # Clean text - remove numbers, special chars, keep only letters and spaces
            clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Need at least 50 characters for reliable detection
            if len(clean_text) < 50:
                return ''
            
            # Detect language code (e.g., 'en', 'es', 'fr', 'de')
            lang_code = detect(clean_text)
            
            # Map common codes to full language names
            lang_map = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'zh-cn': 'Chinese',
                'zh-tw': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean',
                'ar': 'Arabic',
                'hi': 'Hindi',
                'nl': 'Dutch',
                'pl': 'Polish',
                'tr': 'Turkish',
                'sv': 'Swedish',
                'da': 'Danish',
                'no': 'Norwegian',
                'fi': 'Finnish'
            }
            
            return lang_map.get(lang_code, lang_code.capitalize())
        except Exception as e:
            print(f"Language detection error: {e}")
            return ''
    
    if not PYMUPDF_AVAILABLE:
        return metadata
    
    try:
        doc = fitz.open(pdf_path)
        
        # Get PDF metadata
        pdf_meta = doc.metadata
        
        if pdf_meta:
            metadata['title'] = pdf_meta.get('title', '').strip()
            metadata['author'] = pdf_meta.get('author', '').strip()
            metadata['subject'] = pdf_meta.get('subject', '').strip()
            metadata['keywords'] = pdf_meta.get('keywords', '').strip()
            metadata['creator'] = pdf_meta.get('creator', '').strip()
            metadata['producer'] = pdf_meta.get('producer', '').strip()
            
            # Use subject as description if available
            if metadata['subject']:
                metadata['description'] = metadata['subject']
            
            # Parse creation date if available
            if pdf_meta.get('creationDate'):
                try:
                    # PyMuPDF date format: D:YYYYMMDDHHmmSS
                    date_str = pdf_meta.get('creationDate')
                    if date_str.startswith('D:'):
                        date_str = date_str[2:16]  # Get YYYYMMDDHHMMSS
                        metadata['creation_date'] = datetime.strptime(date_str[:8], '%Y%m%d')
                except:
                    pass
        
        # Get page count
        metadata['pages'] = len(doc)
        
        # Try to extract ISBN and DOI from multiple locations
        isbn_pattern = r'ISBN[:\s-]*([0-9]{13}|[0-9]{10}|[0-9\-]{10,17})'
        doi_pattern = r'DOI[:\s]*([0-9]{2}\.[0-9]{4,}/[^\s]+)'
        
        # Check first 15 pages (copyright page can be anywhere in front matter)
        for page_num in range(min(15, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            
            # Search for ISBN
            if not metadata['isbn']:
                isbn_match = re.search(isbn_pattern, text, re.IGNORECASE)
                if isbn_match:
                    isbn = isbn_match.group(1).replace('-', '').replace(' ', '')
                    if len(isbn) in [10, 13]:  # Valid ISBN length
                        metadata['isbn'] = isbn
                        print(f"✓ Found ISBN on page {page_num + 1}: {metadata['isbn']}", flush=True)
            
            # Search for DOI
            if not metadata['doi']:
                doi_match = re.search(doi_pattern, text, re.IGNORECASE)
                if doi_match:
                    metadata['doi'] = doi_match.group(1)
                    print(f"✓ Found DOI on page {page_num + 1}: {metadata['doi']}", flush=True)
        
        # If not found, check last 3 pages (back cover area)
        if (not metadata['isbn'] or not metadata['doi']) and len(doc) > 0:
            isbn_pattern = r'ISBN[:\s-]*([0-9]{13}|[0-9]{10}|[0-9\-]{10,17})'
            doi_pattern = r'DOI[:\s]*([0-9]{2}\.[0-9]{4,}/[^\s]+)'
            
            for page_num in range(max(0, len(doc) - 3), len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if not metadata['isbn']:
                    isbn_match = re.search(isbn_pattern, text, re.IGNORECASE)
                    if isbn_match:
                        isbn = isbn_match.group(1).replace('-', '').replace(' ', '')
                        if len(isbn) in [10, 13]:
                            metadata['isbn'] = isbn
                            print(f"✓ Found ISBN on page {page_num + 1}: {metadata['isbn']}", flush=True)
                
                if not metadata['doi']:
                    doi_match = re.search(doi_pattern, text, re.IGNORECASE)
                    if doi_match:
                        metadata['doi'] = doi_match.group(1)
                        print(f"✓ Found DOI on page {page_num + 1}: {metadata['doi']}", flush=True)
        
        # Extract publication date from first 10 pages (copyright pages)
        if not metadata['publication_date']:
            # Try to find full dates first (DD Month YYYY, DD/MM/YYYY, etc.)
            date_patterns = [
                # Full date patterns
                (r'(?:Published|First published|Copyright|©)\s*(?:on\s*)?(\d{1,2})[\/\-\s]+(\w+)[\/\-\s]+([12]\d{3})', 'dmy'),  # DD Month YYYY
                (r'(?:Published|First published|Copyright|©)\s*(?:on\s*)?(\w+)\s+(\d{1,2})[,\s]+([12]\d{3})', 'mdy'),  # Month DD, YYYY
                (r'(?:Published|First published|Copyright|©)\s*(?:on\s*)?(\d{1,2})[\/\-](\d{1,2})[\/\-]([12]\d{3})', 'dmy_numeric'),  # DD/MM/YYYY
                # Year-only patterns (fallback)
                (r'(?:Published|First published|Copyright|©)\s*(?:in\s*)?([12]\d{3})', 'year_only'),
                (r'([12]\d{3})\s*(?:by|publication)', 'year_only'),
                (r'Edition\s*[^0-9]*([12]\d{3})', 'year_only')
            ]
            
            month_map = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12',
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            for page_num in range(min(10, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                
                for pattern, format_type in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            if format_type == 'dmy':
                                day = match.group(1).zfill(2)
                                month_str = match.group(2).lower()
                                year = match.group(3)
                                month = month_map.get(month_str[:3], '01')
                                metadata['publication_date'] = f"{day}/{month}/{year}"
                                print(f"✓ Found publication date on page {page_num + 1}: {metadata['publication_date']}", flush=True)
                                break
                            elif format_type == 'mdy':
                                month_str = match.group(1).lower()
                                day = match.group(2).zfill(2)
                                year = match.group(3)
                                month = month_map.get(month_str[:3], '01')
                                metadata['publication_date'] = f"{day}/{month}/{year}"
                                print(f"✓ Found publication date on page {page_num + 1}: {metadata['publication_date']}", flush=True)
                                break
                            elif format_type == 'dmy_numeric':
                                day = match.group(1).zfill(2)
                                month = match.group(2).zfill(2)
                                year = match.group(3)
                                if 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                                    metadata['publication_date'] = f"{day}/{month}/{year}"
                                    print(f"✓ Found publication date on page {page_num + 1}: {metadata['publication_date']}", flush=True)
                                    break
                            elif format_type == 'year_only':
                                year = match.group(1)
                                if 1900 <= int(year) <= 2100:
                                    metadata['publication_date'] = f"01/01/{year}"
                                    print(f"✓ Found publication year on page {page_num + 1}: {year} (formatted as 01/01/{year})", flush=True)
                                    break
                        except:
                            continue
                
                if metadata['publication_date']:
                    break
        
        # If STILL not found and OCR available, try OCR on copyright page (usually page 2-4)
        if (not metadata['isbn'] or not metadata['doi']) and OCR_AVAILABLE:
            print("📖 ISBN/DOI not found in text, trying OCR on copyright page...", flush=True)
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write("\n📖 Attempting OCR ISBN/DOI extraction from copyright page...\n")
            
            isbn_pattern = r'ISBN[:\s-]*([0-9]{13}|[0-9]{10}|[0-9\-]{10,17})'
            doi_pattern = r'DOI[:\s]*([0-9]{2}\.[0-9]{4,}/[^\s]+)'
            
            for page_num in range(1, min(5, len(doc))):  # Check pages 2-5
                try:
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    
                    if not metadata['isbn']:
                        isbn_match = re.search(isbn_pattern, ocr_text, re.IGNORECASE)
                        if isbn_match:
                            isbn = isbn_match.group(1).replace('-', '').replace(' ', '')
                            if len(isbn) in [10, 13]:
                                metadata['isbn'] = isbn
                                print(f"✓ Found ISBN via OCR on page {page_num + 1}: {metadata['isbn']}", flush=True)
                                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"✓ Found ISBN via OCR on page {page_num + 1}: {metadata['isbn']}\n")
                    
                    if not metadata['doi']:
                        doi_match = re.search(doi_pattern, ocr_text, re.IGNORECASE)
                        if doi_match:
                            metadata['doi'] = doi_match.group(1)
                            print(f"✓ Found DOI via OCR on page {page_num + 1}: {metadata['doi']}", flush=True)
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"✓ Found DOI via OCR on page {page_num + 1}: {metadata['doi']}\n")
                    
                    if metadata['isbn'] and metadata['doi']:
                        break
                except Exception as e:
                    continue
        
        doc.close()
        
    except Exception as e:
        print(f"Error extracting PDF metadata: {e}", flush=True)
    
    # If metadata is incomplete, try OCR from cover
    # Write debug to file since Flask swallows print statements
    with open('ocr_debug.log', 'a', encoding='utf-8') as f:
        f.write(f"\n=== OCR Debug ===\n")
        f.write(f"OCR_AVAILABLE={OCR_AVAILABLE}, title='{metadata['title']}', author='{metadata['author']}', isbn='{metadata['isbn']}', doi='{metadata['doi']}'\n")
    
    if OCR_AVAILABLE and (not metadata['title'] or not metadata['author']):
        try:
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write("📖 PDF metadata incomplete, attempting OCR extraction from cover...\n")
            
            cover_text = extract_text_from_cover(pdf_path)
            
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"OCR extracted {len(cover_text)} characters\n")
                f.write(f"RAW OCR TEXT:\n{cover_text}\n")
            
            if cover_text:
                cover_metadata = parse_cover_text(cover_text)
                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"Parsed metadata - Title: '{cover_metadata['title']}', Author: '{cover_metadata['author']}', Publisher: '{cover_metadata.get('publisher', '')}', ISBN: '{cover_metadata['isbn']}'\n")
                
                # Fill in missing fields from OCR (but NOT description - that comes from introduction)
                if not metadata['title'] and cover_metadata['title']:
                    metadata['title'] = cover_metadata['title']
                    print(f"✓ OCR Title: {metadata['title']}", flush=True)
                if not metadata['author'] and cover_metadata['author']:
                    metadata['author'] = cover_metadata['author']
                    print(f"✓ OCR Author: {metadata['author']}", flush=True)
                if not metadata['publisher'] and cover_metadata.get('publisher'):
                    metadata['publisher'] = cover_metadata['publisher']
                    print(f"✓ OCR Publisher: {metadata['publisher']}", flush=True)
                if not metadata['isbn'] and cover_metadata['isbn']:
                    metadata['isbn'] = cover_metadata['isbn']
                    print(f"✓ OCR ISBN: {metadata['isbn']}", flush=True)
        except Exception as e:
            import traceback
            print(f"❌ Error during OCR extraction: {e}", flush=True)
            traceback.print_exc()
    elif not OCR_AVAILABLE:
        print("⚠ OCR not available (Tesseract not configured)")
    
    # If title is still empty or rejected (publisher name), try to extract from page 2 (title page)
    if (not metadata['title'] or len(metadata['title']) < 5) and PYMUPDF_AVAILABLE:
        try:
            print("📖 Searching for title on page 2 (title page)...", flush=True)
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write("\n📖 Searching for title on page 2 (title page)...\n")
            
            doc = fitz.open(pdf_path)
            if len(doc) > 1:  # Check if page 2 exists
                page_text = doc[1].get_text()  # Page 2 is index 1
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                
                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"Page 2 has {len(lines)} lines of text\n")
                
                # Look for title in first 10 lines of page 2
                publisher_keywords = ['manning', 'press', 'publishing', 'publisher', 'ebook', 'provided']
                for i, line in enumerate(lines[:10]):
                    # Skip very short lines (likely page numbers)
                    if len(line) < 10:
                        continue
                    
                    # Skip lines with mostly lowercase (likely descriptions)
                    if sum(c.islower() for c in line) > len(line) * 0.7:
                        continue
                    
                    # Skip publisher names
                    if any(kw in line.lower() for kw in publisher_keywords):
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Skipping publisher line: '{line}'\n")
                        continue
                    
                    # Good candidate if it's Title Case or ALL CAPS, reasonable length
                    if 10 <= len(line) <= 150:
                        # Check if it looks like a title (not URL, email, etc.)
                        if not any(x in line for x in ['http://', 'https://', '@', 'www.']):
                            metadata['title'] = line
                            print(f"✓ Title from page 2: {metadata['title']}", flush=True)
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"✓ Extracted title from page 2: {metadata['title']}\n")
                            break
            
            doc.close()
        except Exception as e:
            print(f"Error extracting title from page 2: {e}", flush=True)
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Error extracting title from page 2: {e}\n")
    
    # If author is still empty or looks invalid (single word, numbers, etc.), try to extract from first page content
    def is_valid_author(author):
        """Check if author name looks valid"""
        if not author:
            return False
        # Invalid if contains numbers or special chars
        if any(c.isdigit() for c in author):
            return False
        # Invalid if only one word (should be first + last name)
        words = author.replace(',', ' ').split()
        if len(words) < 2:
            return False
        return True
    
    if (not metadata['author'] or not is_valid_author(metadata['author'])) and PYMUPDF_AVAILABLE:
        try:
            print("📖 Searching for author on first page content...", flush=True)
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write("\n📖 Searching for author on first page content...\n")
            
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                page_text = doc[0].get_text()
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                
                # Helper function to check if a line looks like a person's name
                def is_person_name(line):
                    words = line.split()
                    if not (2 <= len(words) <= 4):
                        return False
                    if len(line) >= 50:
                        return False
                    # Each word should start with uppercase and contain only letters
                    for word in words:
                        if not word or not word[0].isupper():
                            return False
                        # Check if word contains only letters (no #, numbers, etc)
                        if not all(c.isalpha() or c in ['.', ',', '-', "'"] for c in word):
                            return False
                    # Exclude common non-name words
                    non_name_words = ['programming', 'edition', 'volume', 'series', 'guide', 'introduction', 'advanced', 'complete', 'professional', 'press', 'publishing', 'some', 'view', 'project']
                    if any(word.lower() in non_name_words for word in words):
                        return False
                    return True
                
                # Look for author patterns
                authors = []
                i = 0
                while i < min(30, len(lines)):  # Check first 30 lines
                    line = lines[i]
                    line_lower = line.lower()
                    
                    # Check for "X authors:" pattern
                    if 'author' in line_lower and ':' in line:
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Found authors indicator: '{line}'\n")
                        # Look for names in next few lines (skip non-name lines)
                        for j in range(i + 1, min(i + 15, len(lines))):
                            if is_person_name(lines[j]):
                                authors.append(lines[j])
                                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"Found author: '{lines[j]}'\n")
                                # Keep looking for more consecutive names
                                k = j + 1
                                while k < min(j + 5, len(lines)) and is_person_name(lines[k]):
                                    authors.append(lines[k])
                                    with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                        f.write(f"Found author: '{lines[k]}'\n")
                                    k += 1
                                break  # Found author(s), stop searching
                        if authors:
                            break
                    # Check if line itself looks like a person name (fallback)
                    elif is_person_name(line):
                        authors.append(line)
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Found potential author: '{line}'\n")
                        # Check next few lines for more authors
                        j = i + 1
                        while j < min(i + 5, len(lines)) and is_person_name(lines[j]):
                            authors.append(lines[j])
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Found additional author: '{lines[j]}'\n")
                            j += 1
                        break  # Found author(s), stop searching
                    i += 1
                
                if authors:
                    metadata['author'] = ', '.join(authors)
                    print(f"✓ Authors from first page: {metadata['author']}", flush=True)
                    with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                        f.write(f"✓ Final authors: {metadata['author']}\n")
            
            doc.close()
        except Exception as e:
            print(f"Error extracting authors from first page: {e}", flush=True)
    
    # If description is still empty, extract from introduction/preface page
    if not metadata['description']:
        print("📖 Description still empty, searching for introduction page...", flush=True)
        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
            f.write("\n📖 Searching for introduction/preface page for description...\n")
        
        try:
            doc = fitz.open(pdf_path)
            
            # Look for introduction, preface, overview pages
            intro_keywords = ['introduction', 'preface', 'overview', 'summary', 'abstract', 'foreword', 'about this book']
            intro_page = None
            intro_page_num = -1
            found_keyword = ''
            
            # Search first 30 pages for introduction
            for page_num in range(min(30, len(doc))):
                page = doc[page_num]
                page_text = page.get_text()
                page_text_lower = page_text.lower()
                
                for keyword in intro_keywords:
                    if keyword in page_text_lower:
                        # Check if this is a TOC page (lots of dots)
                        dot_count = page_text.count('.')
                        total_chars = len(page_text)
                        is_toc = (dot_count / total_chars) > 0.1 if total_chars > 0 else False
                        
                        if is_toc:
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"⏭ Page {page_num + 1} has '{keyword}' but looks like TOC (skipping)\n")
                            continue  # Skip TOC pages
                        
                        intro_page = page
                        intro_page_num = page_num
                        found_keyword = keyword
                        print(f"📖 Found '{keyword}' on page {page_num + 1}", flush=True)
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"✓ Found '{keyword}' on page {page_num + 1} (actual content)\n")
                        break
                
                if intro_page:
                    break
            
            # If no introduction found, use first content page (skip first 3 pages)
            if not intro_page and len(doc) > 3:
                intro_page = doc[3]
                intro_page_num = 3
                print(f"📖 Using page 4 for description (no introduction found)", flush=True)
                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                    f.write("ℹ Using page 4 for description (no introduction keyword found)\n")
            elif not intro_page and len(doc) > 0:
                intro_page = doc[0]
                intro_page_num = 0
            
            if intro_page:
                # Collect text from current page AND next 2 pages (for multi-page sections)
                all_lines = []
                for offset in range(3):  # Current page + next 2 pages (usually sufficient for introduction sections)
                    page_idx = intro_page_num + offset
                    if page_idx < len(doc):
                        page = doc[page_idx]
                        page_text = page.get_text()
                        page_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                        all_lines.extend(page_lines)
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Page {page_idx + 1} has {len(page_lines)} lines of text\n")
                
                lines = all_lines
                
                # Find the introduction heading, then extract paragraph AFTER it
                description_lines = []
                found_heading = False
                skip_after_heading = 0
                found_acknowledgments = False
                skip_acknowledgments = 0
                
                with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"Processing lines from introduction section (multiple pages):\n")
                
                for i, line in enumerate(lines):
                    # Look for the heading first
                    if not found_heading and found_keyword and found_keyword in line.lower():
                        found_heading = True
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Found heading: '{line}'\n")
                        
                        # Only extract title from heading if we don't already have one
                        # AND it looks like an actual paper title (not section headings)
                        section_keywords = ['about this book', 'about the', 'preface', 'foreword', 'contents', 'table of', 'summary', 'abstract']
                        is_section_heading = any(kw in line.lower() for kw in section_keywords)
                        
                        # Only use heading as title if:
                        # 1. We don't have a title yet (or it's just placeholder like 'title'/'untitled')
                        # 2. It's NOT a section heading
                        # 3. It's reasonably long (>20 chars)
                        if (not metadata['title'] or metadata['title'].lower() in ['title', 'untitled']) and not is_section_heading and len(line) > 20:
                            # This looks like an actual paper/article title
                            metadata['title'] = line.strip()
                            print(f"✓ Extracted title from heading: {metadata['title']}", flush=True)
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"✓ Extracted title from heading: {metadata['title']}\n")
                        elif metadata['title']:
                            # Already have a title, don't overwrite
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Skipping heading as title (already have: '{metadata['title']}')\n")
                        continue
                    
                    # Log lines after heading for debugging
                    if found_heading and len(description_lines) < 5:
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Line {i}: len={len(line)}, text='{line[:80]}'\n")
                    
                    # Skip lines after heading to get past TOC/navigation content
                    if found_heading and skip_after_heading < 700:  # Manning books have extremely long TOCs + acknowledgments spanning many pages
                        # Check if line looks like TOC or navigation (dots, page numbers, short entries)
                        dot_count = line.count('.') + line.count('_') + line.count('-')
                        digit_count = sum(c.isdigit() for c in line)
                        ends_with_number = re.search(r'\d+\s*$', line)
                        
                        # Check for chapter/section numbering at start (e.g., "1.2", "2.1", "Chapter 3")
                        has_chapter_number = re.match(r'^\s*(\d+\.?\d*\s+|Chapter\s+\d+|CHAPTER\s+\d+)', line)
                        
                        # Check for TOC keywords
                        toc_keywords = ['contents', 'acknowledgment', 'foreword', 'preface', 'introduction', 
                                       'appendix', 'glossary', 'index', 'part 1', 'part 2', 'part 3', 
                                       'about this book', 'about the book']
                        has_toc_keyword = any(kw in line.lower() for kw in toc_keywords)
                        
                        # Skip if it looks like TOC entry:
                        # - Has lots of dots/dashes (TOC leaders)
                        # - Ends with page number
                        # - Has high digit percentage
                        # - Is very short (<50 chars)
                        # - Starts with chapter/section number
                        # - Contains TOC keywords
                        is_toc_like = (
                            dot_count > 3 or 
                            ends_with_number or 
                            digit_count > len(line) * 0.15 or
                            len(line) < 50 or
                            line.count('■') > 0 or  # Bullet points
                            has_chapter_number or
                            has_toc_keyword
                        )
                        
                        if is_toc_like:
                            skip_after_heading += 1
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Skipping TOC/nav line {skip_after_heading}: '{line[:60]}'\n")
                            continue
                        
                        # Found a proper paragraph line (long, mostly letters, no TOC markers)
                        letter_count = sum(c.isalpha() for c in line)
                        if len(line) >= 80 and letter_count > len(line) * 0.7:
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"✓ Found description paragraph: '{line[:80]}'\n")
                            skip_after_heading = 999  # Done skipping
                        else:
                            skip_after_heading += 1
                            continue
                    
                    # After skipping TOC, check for acknowledgments section before collecting description
                    if skip_after_heading >= 700 and not found_acknowledgments and 'acknowledgment' in line.lower():
                        found_acknowledgments = True
                        skip_acknowledgments = 0
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Found acknowledgments section (after TOC) at line {i}: '{line}'\n")
                        continue
                    
                    # Skip acknowledgments section content (personal narrative)
                    if found_acknowledgments and skip_acknowledgments < 150:
                        skip_acknowledgments += 1
                        if skip_acknowledgments <= 5:  # Log first few lines
                            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Skipping acknowledgments content line {skip_acknowledgments}: '{line[:60]}'\n")
                        continue
                    
                    # If we haven't found heading yet, skip short lines
                    if not found_heading and len(line) < 20:
                        continue
                    
                    # Skip page numbers and very short lines
                    if line.isdigit() or len(line) < 20:
                        continue
                    
                    # Skip lines with mostly dots or special chars (TOC entries)
                    dot_count = line.count('.') + line.count('_') + line.count('-')
                    if dot_count > len(line) * 0.2:  # More than 20% dots/dashes (stricter)
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Skipping TOC line: '{line[:50]}'\n")
                        continue
                    
                    # Skip lines that are mostly numbers (chapter/page references)
                    digit_count = sum(c.isdigit() for c in line)
                    if digit_count > len(line) * 0.3:
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"Skipping number-heavy line: '{line[:50]}'\n")
                        continue
                    
                    # Skip lines that look like headers or page references (end with numbers)
                    if re.search(r'\d+\s*$', line):
                        continue
                    
                    # Collect paragraph lines (must have mostly letters)
                    letter_count = sum(c.isalpha() for c in line)
                    if letter_count < len(line) * 0.5:  # Less than 50% letters
                        continue
                    
                    description_lines.append(line)
                    current_desc = ' '.join(description_lines)
                    
                    # Collect 200-800 characters to get complete sentences
                    if len(current_desc) >= 200:
                        # Try to end at a sentence boundary (period followed by space or end)
                        if len(current_desc) > 800:
                            # Find last period before 800 chars
                            truncate_pos = current_desc[:800].rfind('. ')
                            if truncate_pos > 200:
                                current_desc = current_desc[:truncate_pos + 1]
                            else:
                                # Try just period at end
                                truncate_pos = current_desc[:800].rfind('.')
                                if truncate_pos > 200:
                                    current_desc = current_desc[:truncate_pos + 1]
                        else:
                            # Check if we already have a complete sentence
                            if current_desc.endswith('.'):
                                pass  # Already complete
                            elif '. ' in current_desc:
                                # End at last sentence
                                truncate_pos = current_desc.rfind('. ')
                                current_desc = current_desc[:truncate_pos + 1]
                        
                        metadata['description'] = current_desc.strip()
                        print(f"✓ Extracted description from page {intro_page_num + 1}: {len(current_desc)} chars", flush=True)
                        with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"✓ Extracted description: {len(current_desc)} chars\n")
                            f.write(f"Description text: {current_desc}\n")
                        break
                
                if not metadata['description'] and description_lines:
                    metadata['description'] = ' '.join(description_lines)[:600]
                    with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                        f.write(f"✓ Extracted partial description: {len(metadata['description'])} chars\n")
                
                if not metadata['description']:
                    with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                        f.write("⚠ No suitable description paragraph found\n")
            
            doc.close()
        except Exception as e:
            print(f"Error extracting description: {e}", flush=True)
            with open('ocr_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"❌ Error extracting description: {e}\n")
    
    # Detect language from available text
    if not metadata['language']:
        print("🌍 Detecting book language...")
        # Try to get text sample for language detection
        text_for_detection = ''
        
        # Prefer description if available (already cleaned)
        if metadata['description']:
            text_for_detection = metadata['description']
        else:
            # Otherwise use first few pages
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(min(5, len(doc))):
                    page = doc[page_num]
                    text_for_detection += page.get_text()
                    if len(text_for_detection) > 500:
                        break
                doc.close()
            except:
                pass
        
        if text_for_detection:
            detected_lang = detect_language_from_text(text_for_detection)
            if detected_lang:
                metadata['language'] = detected_lang
                print(f"✓ Detected language: {detected_lang}")
            else:
                print("⚠ Could not detect language")
    
    return metadata
