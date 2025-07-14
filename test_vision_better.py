#!/usr/bin/env python3
"""Create a proper test image with text for Vision API testing"""

import requests
import base64
import os
from io import BytesIO

# Set up API key
api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyC3k4pkiXJfsdOD6ZO5kOxUDkU7SwXKHZE')

def create_better_test_image():
    """Create a test image with readable text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a larger white background image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add multiple lines of text
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        draw.text((20, 50), "HELLO WORLD", fill='black', font=font)
        draw.text((20, 80), "This is a test", fill='black', font=font)
        draw.text((20, 110), "OCR Document", fill='black', font=font)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_b64
        
    except ImportError:
        # Create a basic image pattern that Vision API can recognize
        # This is a simple black and white pattern
        return "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAALklEQVR42mNkYGD4z8jIyMDIyMjAyMjIwMjIyMDIyMjAyMjIwMjIyMDIyMjAyMgIAGJEAQHKjNHWAAAAAElFTkSuQmCC"

def test_vision_with_proper_image():
    """Test Google Vision API with a proper test image"""
    print("Testing Google Vision API with proper test image...")
    
    # Get base64 image
    test_image = create_better_test_image()
    print(f"Image size: {len(test_image)} characters")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [{
            "image": {"content": test_image},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Vision API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Vision API Response: {result}")
            
            if 'responses' in result and len(result['responses']) > 0:
                resp = result['responses'][0]
                
                # Check for errors in the response
                if 'error' in resp:
                    print(f"❌ Vision API Error: {resp['error']}")
                    return False
                
                if 'textAnnotations' in resp and len(resp['textAnnotations']) > 0:
                    text = resp['textAnnotations'][0]['description']
                    print(f"✅ Extracted text: '{text}'")
                    return True
                else:
                    print("❌ No text annotations found, but no error either")
                    print("This might be because the image has no recognizable text")
                    return False
            else:
                print("❌ No responses in result")
        else:
            print(f"❌ Vision API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Vision API Exception: {e}")
    
    return False

if __name__ == "__main__":
    print(f"API Key: {api_key[:20]}...")
    print("=" * 50)
    
    vision_ok = test_vision_with_proper_image()
    
    print("\n" + "=" * 50)
    print(f"Vision API: {'✅ PASSED' if vision_ok else '❌ FAILED'}")