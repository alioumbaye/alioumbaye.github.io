#!/usr/bin/env python3
"""Test the new Google Vision API approaches"""

import requests
import base64
import os
from io import BytesIO

# Set up API key
api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyC3k4pkiXJfsdOD6ZO5kOxUDkU7SwXKHZE')
BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_text_rich_image():
    """Create an image with clear, readable text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a larger image with high contrast
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to get a larger font
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add multiple lines of clear text
        lines = [
            "HELLO WORLD",
            "This is a test document",
            "for OCR processing",
            "TAHAWU AI Testing",
            "Document Translation"
        ]
        
        y_position = 50
        for line in lines:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 40
        
        # Add some numbers and symbols
        draw.text((50, y_position + 20), "123 Test Street", fill='black', font=font)
        draw.text((50, y_position + 60), "Phone: (555) 123-4567", fill='black', font=font)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_b64}"
        
    except ImportError:
        print("PIL not available, using fallback image...")
        # Create a simple text-based image using a different approach
        # This is a larger PNG with a pattern that might be recognizable
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAAGklEQVR42mNgGAWjYBSMglEwCkbBKBgFQwMAAAYAAAE="

def test_backend_ocr():
    """Test the backend OCR functionality"""
    print("Testing TAHAWU AI backend OCR with new approaches...")
    
    # Create test image
    test_image = create_text_rich_image()
    print(f"Created test image with {len(test_image)} characters")
    
    # Test with Italian translation
    try:
        payload = {
            "base64_image": test_image,
            "target_language": "italian",
            "filename": "test_ocr_document.png"
        }
        
        print("Sending request to backend...")
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OCR + Translation SUCCESS!")
            print(f"Original text: {result.get('original_text', 'N/A')[:100]}...")
            print(f"Translated text: {result.get('translated_text', 'N/A')[:100]}...")
            print(f"Detected language: {result.get('detected_language', 'N/A')}")
            print(f"Target language: {result.get('target_language', 'N/A')}")
            return True
        else:
            print(f"❌ OCR + Translation FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

def test_simple_translation():
    """Test simple translation to verify backend is working"""
    print("\nTesting simple translation...")
    
    try:
        data = {
            "text": "Hello, this is a test document",
            "target_language": "italian"
        }
        
        response = requests.post(f"{BACKEND_URL}/translate-text", data=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Translation SUCCESS!")
            print(f"Original: {result.get('original_text', 'N/A')}")
            print(f"Translated: {result.get('translated_text', 'N/A')}")
            return True
        else:
            print(f"❌ Translation FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Translation Exception: {e}")
        return False

if __name__ == "__main__":
    print("TAHAWU AI - Testing New Vision API Approaches")
    print("=" * 60)
    
    # Test simple translation first
    translation_ok = test_simple_translation()
    
    # Test OCR + Translation
    ocr_ok = test_backend_ocr()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Translation Only: {'✅ PASSED' if translation_ok else '❌ FAILED'}")
    print(f"OCR + Translation: {'✅ PASSED' if ocr_ok else '❌ FAILED'}")
    
    if translation_ok and not ocr_ok:
        print("\n💡 The translation functionality is working perfectly!")
        print("   OCR might need additional Google Cloud Vision API setup.")
    elif ocr_ok:
        print("\n🎉 All functionality is working perfectly!")
    else:
        print("\n⚠️  Both tests failed - please check backend logs.")