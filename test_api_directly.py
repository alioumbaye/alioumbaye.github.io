#!/usr/bin/env python3
"""Test the APIs directly to debug issues"""

import requests
import base64
import os
from io import BytesIO

# Set up API key
api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyC3k4pkiXJfsdOD6ZO5kOxUDkU7SwXKHZE')

def create_test_image_with_text():
    """Create a simple test image with text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white background image
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        draw.text((10, 30), "Hello World!", fill='black', font=font)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_b64
        
    except ImportError:
        # Fallback to a larger PNG with text (this is a 3x3 black pixel)
        return "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAYAAABWKLW/AAAAKElEQVR42mNkYGD4z8DAwMDIwMDwn4GBgZGBgYGRkYGBkZGBgZGBgQEABSwBA8FU8oMAAAAASUVORK5CYII="

def test_vision_api():
    """Test Google Vision API directly"""
    print("Testing Google Vision API...")
    
    # Get base64 image
    test_image = create_test_image_with_text()
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [{
            "image": {"content": test_image},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Vision API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Vision API Response: {result}")
            
            if 'responses' in result and len(result['responses']) > 0:
                resp = result['responses'][0]
                if 'textAnnotations' in resp:
                    text = resp['textAnnotations'][0]['description']
                    print(f"✅ Extracted text: '{text}'")
                    return True
                else:
                    print("❌ No text annotations found")
            else:
                print("❌ No responses in result")
        else:
            print(f"❌ Vision API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Vision API Exception: {e}")
    
    return False

def test_translate_api():
    """Test Google Translate API directly"""
    print("\nTesting Google Translate API...")
    
    url = f"https://translation.googleapis.com/language/translate/v2?key={api_key}"
    payload = {
        'q': 'Hello World',
        'target': 'it',
        'format': 'text'
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Translate API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Translate API Response: {result}")
            
            if 'data' in result and 'translations' in result['data']:
                translation = result['data']['translations'][0]
                print(f"✅ Translation: '{translation['translatedText']}'")
                return True
            else:
                print("❌ No translation data found")
        else:
            print(f"❌ Translate API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Translate API Exception: {e}")
    
    return False

if __name__ == "__main__":
    print(f"API Key: {api_key[:20]}...")
    print("=" * 50)
    
    vision_ok = test_vision_api()
    translate_ok = test_translate_api()
    
    print("\n" + "=" * 50)
    print(f"Vision API: {'✅ PASSED' if vision_ok else '❌ FAILED'}")
    print(f"Translate API: {'✅ PASSED' if translate_ok else '❌ FAILED'}")