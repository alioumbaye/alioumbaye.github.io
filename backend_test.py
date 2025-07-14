#!/usr/bin/env python3
"""
Comprehensive Backend Testing for TAHAWU AI
Tests Google Cloud Vision OCR, Google Translate API, Document Analysis, and Translation History
"""

import requests
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any
import os

# Backend URL from frontend/.env
BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

class TAHAWUBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = {
            "ocr_integration": {"passed": False, "details": []},
            "translate_integration": {"passed": False, "details": []},
            "document_analysis": {"passed": False, "details": []},
            "translation_history": {"passed": False, "details": []}
        }
        
    def create_test_image_base64(self, text_content: str = "Hello World! This is a test document.") -> str:
        """Create a simple test image with text as base64"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a simple white image with black text
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw text on image
            draw.text((20, 50), text_content, fill='black', font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/png;base64,{img_base64}"
            
        except ImportError:
            # Fallback: Create a minimal base64 encoded PNG
            # This is a 1x1 white PNG pixel
            minimal_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            return f"data:image/png;base64,{minimal_png}"
    
    def test_basic_connectivity(self) -> bool:
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ Backend connectivity: PASSED")
                return True
            else:
                print(f"❌ Backend connectivity: FAILED - Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connectivity: FAILED - {str(e)}")
            return False
    
    def test_ocr_integration(self) -> bool:
        """Test Google Cloud Vision OCR API Integration"""
        print("\n🔍 Testing Google Cloud Vision OCR API Integration...")
        
        try:
            # Test with a simple text image
            test_image = self.create_test_image_base64("Hello World Test OCR")
            
            # Test analyze-document endpoint (which uses OCR internally)
            payload = {
                "base64_image": test_image,
                "target_language": "italian",
                "filename": "test_ocr.png"
            }
            
            response = requests.post(
                f"{self.backend_url}/analyze-document",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("original_text"):
                    self.test_results["ocr_integration"]["passed"] = True
                    self.test_results["ocr_integration"]["details"].append(
                        f"✅ OCR extracted text: '{result['original_text'][:50]}...'"
                    )
                    print("✅ OCR Integration: PASSED")
                    return True
                else:
                    self.test_results["ocr_integration"]["details"].append(
                        f"❌ OCR returned no text or failed: {result}"
                    )
            else:
                self.test_results["ocr_integration"]["details"].append(
                    f"❌ OCR API call failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.test_results["ocr_integration"]["details"].append(f"❌ OCR test error: {str(e)}")
        
        print("❌ OCR Integration: FAILED")
        return False
    
    def test_translate_integration(self) -> bool:
        """Test Google Translate API Integration"""
        print("\n🌐 Testing Google Translate API Integration...")
        
        test_languages = ["italian", "french", "wolof"]
        test_text = "Hello, how are you today?"
        
        all_passed = True
        
        for lang in test_languages:
            try:
                # Test direct translation endpoint
                payload = {
                    "text": test_text,
                    "target_language": lang
                }
                
                response = requests.post(
                    f"{self.backend_url}/translate-text",
                    data=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result.get("translated_text"):
                        self.test_results["translate_integration"]["details"].append(
                            f"✅ {lang.capitalize()}: '{result['translated_text'][:50]}...'"
                        )
                        print(f"✅ Translation to {lang}: PASSED")
                    else:
                        self.test_results["translate_integration"]["details"].append(
                            f"❌ {lang.capitalize()}: No translation returned"
                        )
                        all_passed = False
                        print(f"❌ Translation to {lang}: FAILED - No translation")
                else:
                    self.test_results["translate_integration"]["details"].append(
                        f"❌ {lang.capitalize()}: API error {response.status_code}"
                    )
                    all_passed = False
                    print(f"❌ Translation to {lang}: FAILED - Status {response.status_code}")
                    
            except Exception as e:
                self.test_results["translate_integration"]["details"].append(
                    f"❌ {lang.capitalize()}: Exception {str(e)}"
                )
                all_passed = False
                print(f"❌ Translation to {lang}: FAILED - {str(e)}")
        
        self.test_results["translate_integration"]["passed"] = all_passed
        return all_passed
    
    def test_document_analysis_workflow(self) -> bool:
        """Test complete Document Analysis Endpoint workflow"""
        print("\n📄 Testing Document Analysis Workflow...")
        
        try:
            # Create test image with meaningful text
            test_image = self.create_test_image_base64("Document analysis test with sample text")
            
            # Test all target languages
            test_languages = ["italian", "french", "wolof"]
            all_passed = True
            
            for lang in test_languages:
                try:
                    payload = {
                        "base64_image": test_image,
                        "target_language": lang,
                        "filename": f"test_document_{lang}.png"
                    }
                    
                    response = requests.post(
                        f"{self.backend_url}/analyze-document",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Verify response structure
                        required_fields = ["success", "original_text", "translated_text", 
                                         "detected_language", "target_language", "timestamp"]
                        
                        if all(field in result for field in required_fields):
                            if result["success"] and result["original_text"] and result["translated_text"]:
                                self.test_results["document_analysis"]["details"].append(
                                    f"✅ {lang.capitalize()}: Complete workflow successful"
                                )
                                print(f"✅ Document Analysis ({lang}): PASSED")
                            else:
                                self.test_results["document_analysis"]["details"].append(
                                    f"❌ {lang.capitalize()}: Missing text data"
                                )
                                all_passed = False
                        else:
                            missing_fields = [f for f in required_fields if f not in result]
                            self.test_results["document_analysis"]["details"].append(
                                f"❌ {lang.capitalize()}: Missing fields: {missing_fields}"
                            )
                            all_passed = False
                    else:
                        self.test_results["document_analysis"]["details"].append(
                            f"❌ {lang.capitalize()}: API error {response.status_code}"
                        )
                        all_passed = False
                        
                except Exception as e:
                    self.test_results["document_analysis"]["details"].append(
                        f"❌ {lang.capitalize()}: Exception {str(e)}"
                    )
                    all_passed = False
                    
                # Small delay between requests
                time.sleep(1)
            
            self.test_results["document_analysis"]["passed"] = all_passed
            return all_passed
            
        except Exception as e:
            self.test_results["document_analysis"]["details"].append(f"❌ Workflow test error: {str(e)}")
            print(f"❌ Document Analysis Workflow: FAILED - {str(e)}")
            return False
    
    def test_translation_history_storage(self) -> bool:
        """Test Translation History Storage and Retrieval"""
        print("\n💾 Testing Translation History Storage...")
        
        try:
            # First, create some translation history by using analyze-document
            test_image = self.create_test_image_base64("History test document content")
            
            payload = {
                "base64_image": test_image,
                "target_language": "italian",
                "filename": "history_test.png"
            }
            
            # Create a translation to store in history
            response = requests.post(
                f"{self.backend_url}/analyze-document",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                self.test_results["translation_history"]["details"].append(
                    f"❌ Failed to create test translation: {response.status_code}"
                )
                return False
            
            # Wait a moment for database write
            time.sleep(2)
            
            # Now test retrieving translation history
            history_response = requests.get(
                f"{self.backend_url}/translation-history",
                timeout=15
            )
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                
                if isinstance(history_data, list):
                    if len(history_data) > 0:
                        # Verify history entry structure
                        entry = history_data[0]
                        required_fields = ["id", "original_text", "translated_text", 
                                         "detected_language", "target_language", 
                                         "filename", "timestamp"]
                        
                        if all(field in entry for field in required_fields):
                            self.test_results["translation_history"]["passed"] = True
                            self.test_results["translation_history"]["details"].append(
                                f"✅ History retrieved: {len(history_data)} entries"
                            )
                            self.test_results["translation_history"]["details"].append(
                                f"✅ Entry structure valid with all required fields"
                            )
                            print("✅ Translation History Storage: PASSED")
                            return True
                        else:
                            missing_fields = [f for f in required_fields if f not in entry]
                            self.test_results["translation_history"]["details"].append(
                                f"❌ Missing fields in history entry: {missing_fields}"
                            )
                    else:
                        self.test_results["translation_history"]["details"].append(
                            "❌ No history entries found after creating translation"
                        )
                else:
                    self.test_results["translation_history"]["details"].append(
                        f"❌ History response not a list: {type(history_data)}"
                    )
            else:
                self.test_results["translation_history"]["details"].append(
                    f"❌ History API error: {history_response.status_code}"
                )
                
        except Exception as e:
            self.test_results["translation_history"]["details"].append(
                f"❌ History test error: {str(e)}"
            )
        
        print("❌ Translation History Storage: FAILED")
        return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid inputs"""
        print("\n⚠️  Testing Error Handling...")
        
        error_tests = [
            {
                "name": "Invalid base64 image",
                "payload": {
                    "base64_image": "invalid_base64_data",
                    "target_language": "italian",
                    "filename": "test.png"
                },
                "expected_status": [400, 500]
            },
            {
                "name": "Empty base64 image",
                "payload": {
                    "base64_image": "",
                    "target_language": "italian",
                    "filename": "test.png"
                },
                "expected_status": [400, 422, 500]
            },
            {
                "name": "Invalid target language",
                "payload": {
                    "base64_image": self.create_test_image_base64("Test"),
                    "target_language": "invalid_language",
                    "filename": "test.png"
                },
                "expected_status": [400, 500]
            }
        ]
        
        passed_tests = 0
        
        for test in error_tests:
            try:
                response = requests.post(
                    f"{self.backend_url}/analyze-document",
                    json=test["payload"],
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code in test["expected_status"]:
                    print(f"✅ {test['name']}: Properly handled (Status {response.status_code})")
                    passed_tests += 1
                else:
                    print(f"❌ {test['name']}: Unexpected status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {test['name']}: Exception {str(e)}")
        
        return passed_tests == len(error_tests)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting TAHAWU AI Backend Testing...")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_connectivity():
            return {"error": "Backend not accessible"}
        
        # Run all tests
        test_methods = [
            ("OCR Integration", self.test_ocr_integration),
            ("Translate Integration", self.test_translate_integration),
            ("Document Analysis Workflow", self.test_document_analysis_workflow),
            ("Translation History Storage", self.test_translation_history_storage)
        ]
        
        overall_results = {}
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                overall_results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name}: CRITICAL ERROR - {str(e)}")
                overall_results[test_name] = False
        
        # Test error handling (optional)
        print("\n" + "=" * 60)
        error_handling_result = self.test_error_handling()
        overall_results["Error Handling"] = error_handling_result
        
        return {
            "overall_results": overall_results,
            "detailed_results": self.test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TAHAWU AI Backend Test Summary")
        print("=" * 60)
        
        if "error" in results:
            print(f"❌ CRITICAL: {results['error']}")
            return
        
        overall = results["overall_results"]
        detailed = results["detailed_results"]
        
        # Print overall results
        for test_name, passed in overall.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        # Print detailed results
        print("\n📋 Detailed Results:")
        for test_key, test_data in detailed.items():
            print(f"\n{test_key.replace('_', ' ').title()}:")
            for detail in test_data["details"]:
                print(f"  {detail}")
        
        # Calculate pass rate
        passed_count = sum(1 for result in overall.values() if result)
        total_count = len(overall)
        pass_rate = (passed_count / total_count) * 100
        
        print(f"\n🎯 Overall Pass Rate: {passed_count}/{total_count} ({pass_rate:.1f}%)")
        
        if pass_rate >= 75:
            print("🎉 Backend testing: MOSTLY SUCCESSFUL")
        elif pass_rate >= 50:
            print("⚠️  Backend testing: PARTIALLY SUCCESSFUL")
        else:
            print("❌ Backend testing: NEEDS ATTENTION")

def main():
    """Main test execution"""
    tester = TAHAWUBackendTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    return results

if __name__ == "__main__":
    main()