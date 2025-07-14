#!/usr/bin/env python3
"""Test Vision API with a simple text image created manually"""

import requests
import base64
import os

# Set up API key
api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyC3k4pkiXJfsdOD6ZO5kOxUDkU7SwXKHZE')
BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_simple_text_image():
    """Create a simple image with text using basic PIL"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple black text on white background
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Use default font and draw simple text
        draw.text((20, 30), "HELLO", fill='black')
        draw.text((20, 50), "WORLD", fill='black')
        
        # Convert to base64
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_b64}"
        
    except ImportError:
        print("PIL not available, creating manual base64 image...")
        # This is a simple 8x8 black and white checkerboard pattern
        # Not ideal for OCR but better than a solid color
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAJklEQVR42mP8/5+BgYGBgYmJiYGBgYmJiYGBgYmJiYGBgYmJiYGBgQEAJwgEAMvwY0YAAAAASUVORK5CYII="

def test_with_simple_image():
    """Test with a very simple image"""
    print("Testing with simple manually created image...")
    
    # Create simple test image
    test_image = create_simple_text_image()
    print(f"Created image with {len(test_image)} characters")
    
    try:
        payload = {
            "base64_image": test_image,
            "target_language": "italian",
            "filename": "simple_test.png"
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
            print("✅ SUCCESS!")
            print(f"Original text: '{result.get('original_text', 'N/A')}'")
            print(f"Translated text: '{result.get('translated_text', 'N/A')}'")
            print(f"Detected language: {result.get('detected_language', 'N/A')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing Vision API with Simple Image")
    print("=" * 50)
    
    success = test_with_simple_image()
    
    print("\n" + "=" * 50)
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if not success:
        print("\n💡 Trying to test Google Vision API directly...")
        
        # Direct API test
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            payload = {
                "requests": [{
                    "image": {"content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="},
                    "features": [{"type": "TEXT_DETECTION"}]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            print(f"Direct API Status: {response.status_code}")
            print(f"Direct API Response: {response.text}")
            
        except Exception as e:
            print(f"Direct API Exception: {e}")