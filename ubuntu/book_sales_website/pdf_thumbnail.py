"""
PDF Thumbnail Generation Helper

This module provides functions to extract the first page of a PDF
and convert it to a thumbnail image.
"""

import os
from PIL import Image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

def generate_pdf_thumbnail(pdf_path, output_path, max_width=300, max_height=450):
    """
    Generate a thumbnail image from the first page of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path where the thumbnail should be saved
        max_width: Maximum width of the thumbnail (default: 300)
        max_height: Maximum height of the thumbnail (default: 450)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Try PyMuPDF first (faster and more reliable)
    if PYMUPDF_AVAILABLE:
        try:
            return _generate_thumbnail_pymupdf(pdf_path, output_path, max_width, max_height)
        except Exception as e:
            print(f"PyMuPDF failed: {e}")
            # Fall through to try pdf2image
    
    # Try pdf2image as fallback
    if PDF2IMAGE_AVAILABLE:
        try:
            return _generate_thumbnail_pdf2image(pdf_path, output_path, max_width, max_height)
        except Exception as e:
            print(f"pdf2image failed: {e}")
            return False
    
    print("No PDF processing library available. Install PyMuPDF (fitz) or pdf2image.")
    return False

def _generate_thumbnail_pymupdf(pdf_path, output_path, max_width, max_height):
    """Generate thumbnail using PyMuPDF (fitz)"""
    doc = fitz.open(pdf_path)
    
    if len(doc) == 0:
        return False
    
    # Get first page
    page = doc[0]
    
    # Calculate zoom to fit within max dimensions
    rect = page.rect
    zoom_x = max_width / rect.width
    zoom_y = max_height / rect.height
    zoom = min(zoom_x, zoom_y)
    
    # Render page to pixmap
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Save as PNG
    pix.save(output_path)
    doc.close()
    
    return True

def _generate_thumbnail_pdf2image(pdf_path, output_path, max_width, max_height):
    """Generate thumbnail using pdf2image"""
    # Convert first page only
    images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
    
    if not images:
        return False
    
    # Get first page
    img = images[0]
    
    # Resize to fit within max dimensions
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Save as PNG
    img.save(output_path, 'PNG', optimize=True)
    
    return True
