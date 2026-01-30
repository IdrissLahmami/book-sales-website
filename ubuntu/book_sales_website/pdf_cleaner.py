"""
PDF Page Removal and Cleaning Utilities
"""
import fitz  # PyMuPDF
import re
import os


def detect_watermark_pages(pdf_path):
    """
    Detect pages that appear to be watermarks or advertisements.
    Returns list of page numbers (0-indexed) that are likely watermarks.
    """
    watermark_pages = []
    
    # Common watermark patterns
    watermark_patterns = [
        r'plentyofebooks',
        r'free\s*ebooks?\s*download',
        r'uploaded\s*by',
        r'this\s*ebook\s*is\s*provided\s*by',
        r'visit\s*www\.',
        r'download\s*more\s*ebooks?',
        r'ebookee\.com',
        r'ebook3000',
        r'freebookspot',
        r'all\s*IT\s*eBooks',
        r'foxebook',
        r'free\s*pdf\s*books'
    ]
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()
            
            # Check for watermark patterns
            for pattern in watermark_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    watermark_pages.append(page_num)
                    print(f"📍 Detected watermark on page {page_num + 1}: pattern '{pattern}'")
                    break
            
            # Check for very short pages (likely ads)
            if len(text.strip()) < 100 and 'www.' in text:
                if page_num not in watermark_pages:
                    watermark_pages.append(page_num)
                    print(f"📍 Detected short ad page {page_num + 1}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error detecting watermarks: {e}")
    
    return watermark_pages


def remove_pages(pdf_path, pages_to_remove, output_path=None):
    """
    Remove specified pages from a PDF.
    
    Args:
        pdf_path: Path to input PDF
        pages_to_remove: List of page numbers to remove (0-indexed)
        output_path: Path for cleaned PDF (if None, creates temp file then overwrites)
    
    Returns:
        str: Path to cleaned PDF
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Sort pages in reverse order to avoid index shifting
        pages_to_remove = sorted(set(pages_to_remove), reverse=True)
        
        print(f"📄 Removing {len(pages_to_remove)} pages from PDF...")
        
        for page_num in pages_to_remove:
            if 0 <= page_num < len(doc):
                doc.delete_page(page_num)
                print(f"  ✓ Removed page {page_num + 1}")
        
        # Save to a temporary file first, then rename
        if output_path is None:
            output_path = pdf_path + ".tmp"
            temp_file = True
        else:
            temp_file = False
        
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        # If we saved to temp, replace original
        if temp_file:
            import shutil
            shutil.move(output_path, pdf_path)
            output_path = pdf_path
        
        print(f"✅ Cleaned PDF saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error removing pages: {e}")
        if 'doc' in locals():
            doc.close()
        raise


def clean_pdf_auto(pdf_path, output_path=None):
    """
    Automatically detect and remove watermark pages from PDF.
    
    Args:
        pdf_path: Path to input PDF
        output_path: Path for cleaned PDF (if None, overwrites original)
    
    Returns:
        dict: {'cleaned_path': str, 'removed_pages': list, 'removed_count': int}
    """
    print(f"🧹 Auto-cleaning PDF: {pdf_path}")
    
    # Detect watermark pages
    watermark_pages = detect_watermark_pages(pdf_path)
    
    if not watermark_pages:
        print("✓ No watermarks detected")
        return {
            'cleaned_path': pdf_path,
            'removed_pages': [],
            'removed_count': 0
        }
    
    print(f"Found {len(watermark_pages)} watermark page(s): {[p+1 for p in watermark_pages]}")
    
    # Remove watermark pages
    cleaned_path = remove_pages(pdf_path, watermark_pages, output_path)
    
    return {
        'cleaned_path': cleaned_path,
        'removed_pages': watermark_pages,
        'removed_count': len(watermark_pages)
    }


def get_page_preview(pdf_path, page_num, max_chars=500):
    """
    Get text preview of a specific page.
    
    Args:
        pdf_path: Path to PDF
        page_num: Page number (0-indexed)
        max_chars: Maximum characters to return
    
    Returns:
        str: Page text preview
    """
    try:
        doc = fitz.open(pdf_path)
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            text = page.get_text()
            doc.close()
            
            # Truncate if too long
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text
        else:
            doc.close()
            return f"Invalid page number: {page_num}"
    except Exception as e:
        return f"Error: {e}"


def get_pdf_info(pdf_path):
    """
    Get information about PDF structure.
    
    Returns:
        dict: PDF information including page count, potential watermarks, etc.
    """
    try:
        doc = fitz.open(pdf_path)
        
        info = {
            'page_count': len(doc),
            'file_size': os.path.getsize(pdf_path),
            'watermark_pages': detect_watermark_pages(pdf_path),
            'metadata': doc.metadata
        }
        
        doc.close()
        return info
        
    except Exception as e:
        return {'error': str(e)}
