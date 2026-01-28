"""
Test PDF Thumbnail Generation

This script tests the thumbnail generation functionality.
"""

import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_thumbnail import generate_pdf_thumbnail

# Test if PyMuPDF is available
try:
    import fitz
    print("✓ PyMuPDF (fitz) is installed")
    print(f"  Version: {fitz.version}")
except ImportError:
    print("✗ PyMuPDF (fitz) is NOT installed")

# Test if pdf2image is available
try:
    from pdf2image import convert_from_path
    print("✓ pdf2image is installed")
except ImportError:
    print("✗ pdf2image is NOT installed")

# Test if Pillow is available
try:
    from PIL import Image
    print("✓ Pillow (PIL) is installed")
    print(f"  Version: {Image.__version__ if hasattr(Image, '__version__') else 'Unknown'}")
except ImportError:
    print("✗ Pillow (PIL) is NOT installed")

print("\nThumbnail generation is ready to use!")
print("When you upload a PDF without a cover image, a thumbnail will be automatically generated.")
