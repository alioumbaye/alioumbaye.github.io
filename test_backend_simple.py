#!/usr/bin/env python3
"""Test the backend endpoints directly"""

import requests
import json

BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def test_translate_endpoint():
    """Test the translate-text endpoint"""
    print("Testing translate-text endpoint...")
    
    # Test Italian
    try:
        data = {
            "text": "Hello, how are you?",
            "target_language": "italian"
        }
        
        response = requests.post(f"{BACKEND_URL}/translate-text", data=data, timeout=15)
        print(f"Italian translation status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Italian result: {result}")
            return True
        else:
            print(f"Italian error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Italian exception: {e}")
        return False

def test_simple_document_analysis():
    """Test document analysis with minimal data"""
    print("\nTesting analyze-document endpoint with minimal data...")
    
    # Use the simplest possible valid base64 image
    simple_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    try:
        payload = {
            "base64_image": simple_base64,
            "target_language": "italian",
            "filename": "test.png"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Document analysis status: {response.status_code}")
        print(f"Document analysis response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Document analysis result: {result}")
            return True
        else:
            print(f"Document analysis error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Document analysis exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing TAHAWU AI Backend Endpoints")
    print("=" * 50)
    
    # Test translation first (this was working)
    translate_ok = test_translate_endpoint()
    
    # Test document analysis
    document_ok = test_simple_document_analysis()
    
    print("\n" + "=" * 50)
    print(f"Translation: {'✅ PASSED' if translate_ok else '❌ FAILED'}")
    print(f"Document Analysis: {'✅ PASSED' if document_ok else '❌ FAILED'}")