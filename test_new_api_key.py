#!/usr/bin/env python3
"""Test the new API key with proper text images"""

import requests
import base64
import os

# New API key
api_key = "AIzaSyCUlVnKoT8wU01RmP3CS2j5lbRfUhK0PxI"
BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_clear_text_image():
    """Create a clear text image with PIL if available"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a large, high-contrast image
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Use default font but make text large and clear
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add multiple lines of clear, readable text
        text_lines = [
            "HELLO WORLD",
            "This is a test document",
            "for OCR processing",
            "TAHAWU AI Testing",
            "Google Cloud Vision API",
            "Document Translation",
            "123 Main Street",
            "Phone: 555-1234"
        ]
        
        y_position = 30
        for line in text_lines:
            draw.text((30, y_position), line, fill='black', font=font)
            y_position += 35
        
        # Convert to base64
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_b64
        
    except ImportError:
        print("PIL not available - using fallback method")
        return None

def test_vision_api_directly():
    """Test Vision API directly with the new key"""
    print("Testing Google Vision API directly with new key...")
    
    # Create test image
    test_image = create_clear_text_image()
    
    if not test_image:
        print("Could not create test image")
        return False
    
    # Test Vision API directly
    try:
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        payload = {
            "requests": [{
                "image": {"content": test_image},
                "features": [{"type": "TEXT_DETECTION"}]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Vision API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Vision API Response: {result}")
            
            if 'responses' in result and len(result['responses']) > 0:
                resp = result['responses'][0]
                
                if 'error' in resp:
                    print(f"❌ Vision API Error: {resp['error']}")
                    return False
                
                if 'textAnnotations' in resp and len(resp['textAnnotations']) > 0:
                    text = resp['textAnnotations'][0]['description']
                    print(f"✅ Vision API SUCCESS! Extracted text: '{text[:100]}...'")
                    return True
                else:
                    print("❌ No text found in image")
                    return False
            else:
                print("❌ No responses in result")
                return False
        else:
            print(f"❌ Vision API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Vision API Exception: {e}")
        return False

def test_backend_ocr():
    """Test the backend OCR functionality"""
    print("\nTesting backend OCR with new API key...")
    
    # Create test image
    test_image = create_clear_text_image()
    
    if not test_image:
        print("Could not create test image")
        return False
    
    try:
        payload = {
            "base64_image": f"data:image/png;base64,{test_image}",
            "target_language": "italian",
            "filename": "test_ocr.png"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Backend OCR Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend OCR SUCCESS!")
            print(f"Original text: '{result.get('original_text', 'N/A')[:100]}...'")
            print(f"Translated text: '{result.get('translated_text', 'N/A')[:100]}...'")
            print(f"Detected language: {result.get('detected_language', 'N/A')}")
            return True
        else:
            print(f"❌ Backend OCR FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Backend OCR Exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing TAHAWU AI with New Google Vision API Key")
    print("=" * 60)
    print(f"New API Key: {api_key[:20]}...")
    print("=" * 60)
    
    # Test Vision API directly first
    vision_direct = test_vision_api_directly()
    
    # Test backend OCR
    backend_ocr = test_backend_ocr()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Vision API Direct: {'✅ PASSED' if vision_direct else '❌ FAILED'}")
    print(f"Backend OCR: {'✅ PASSED' if backend_ocr else '❌ FAILED'}")
    
    if vision_direct and backend_ocr:
        print("\n🎉 SUCCESS! OCR is now working with the new API key!")
    elif vision_direct:
        print("\n💡 Vision API works directly but backend needs restart")
    else:
        print("\n❌ OCR still not working - may need API setup")