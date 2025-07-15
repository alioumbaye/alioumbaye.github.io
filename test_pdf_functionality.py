#!/usr/bin/env python3
"""Test PDF processing functionality"""

import requests
import base64
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_test_pdf():
    """Create a test PDF with text content"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        
        # Create PDF with text content
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add text to the PDF
        p.drawString(100, 750, "TEST DOCUMENT")
        p.drawString(100, 720, "This is a test PDF document")
        p.drawString(100, 690, "for OCR processing with TAHAWU AI")
        p.drawString(100, 660, "Document contains important information")
        p.drawString(100, 630, "Please translate this content")
        p.drawString(100, 600, "Phone: 555-123-4567")
        p.drawString(100, 570, "Email: test@example.com")
        
        # Add page 2
        p.showPage()
        p.drawString(100, 750, "PAGE 2")
        p.drawString(100, 720, "Additional content on second page")
        p.drawString(100, 690, "More text to translate")
        
        p.save()
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Convert to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return f"data:application/pdf;base64,{pdf_base64}"
        
    except ImportError:
        print("reportlab not available, creating simple PDF...")
        # Create minimal PDF manually
        pdf_content = """
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(TEST PDF DOCUMENT) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF
"""
        pdf_base64 = base64.b64encode(pdf_content.encode()).decode('utf-8')
        return f"data:application/pdf;base64,{pdf_base64}"

def test_pdf_processing():
    """Test PDF processing with the backend"""
    print("Testing PDF processing functionality...")
    
    # Create test PDF
    test_pdf = create_test_pdf()
    print(f"Created test PDF with {len(test_pdf)} characters")
    
    # Test with Italian translation
    try:
        payload = {
            "base64_image": test_pdf,
            "target_language": "italian",
            "filename": "test_document.pdf"
        }
        
        print("Sending PDF to backend for processing...")
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF PROCESSING SUCCESS!")
            print(f"Success: {result.get('success', False)}")
            print(f"Original text: {result.get('original_text', 'N/A')[:200]}...")
            print(f"Translated text: {result.get('translated_text', 'N/A')[:200]}...")
            print(f"Explanation: {result.get('explanation', 'N/A')[:200]}...")
            print(f"Detected language: {result.get('detected_language', 'N/A')}")
            print(f"Target language: {result.get('target_language', 'N/A')}")
            return True
        else:
            print(f"❌ PDF PROCESSING FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF Processing Exception: {e}")
        return False

def test_image_processing():
    """Test that regular image processing still works"""
    print("\nTesting regular image processing...")
    
    try:
        from PIL import Image, ImageDraw
        
        # Create test image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "HELLO WORLD", fill='black')
        draw.text((50, 100), "This is a test image", fill='black')
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        payload = {
            "base64_image": f"data:image/png;base64,{img_base64}",
            "target_language": "french",
            "filename": "test_image.png"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ IMAGE PROCESSING SUCCESS!")
            print(f"Original text: {result.get('original_text', 'N/A')}")
            print(f"Translated text: {result.get('translated_text', 'N/A')}")
            return True
        else:
            print(f"❌ IMAGE PROCESSING FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Image Processing Exception: {e}")
        return False

if __name__ == "__main__":
    print("TAHAWU AI - PDF Processing Test")
    print("=" * 50)
    
    # Test PDF processing
    pdf_success = test_pdf_processing()
    
    # Test regular image processing
    image_success = test_image_processing()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"PDF Processing: {'✅ PASSED' if pdf_success else '❌ FAILED'}")
    print(f"Image Processing: {'✅ PASSED' if image_success else '❌ FAILED'}")
    
    if pdf_success and image_success:
        print("\n🎉 ALL TESTS PASSED! PDF and image processing both working!")
    elif pdf_success:
        print("\n💡 PDF processing is working! Image processing needs checking.")
    elif image_success:
        print("\n💡 Image processing is working! PDF processing needs fixing.")
    else:
        print("\n❌ Both tests failed - check backend logs for details.")