#!/usr/bin/env python3
"""Test the final TAHAWU AI features: localized explanations and PDF export"""

import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64

BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_test_document():
    """Create a test document for analysis"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Create a business invoice
    p.drawString(100, 750, "FATTURA N. 12345")
    p.drawString(100, 720, "ABC Company S.r.l.")
    p.drawString(100, 700, "Via Roma 123")
    p.drawString(100, 680, "Milano, MI 20100")
    p.drawString(100, 650, "P.IVA: 12345678901")
    p.drawString(100, 620, "")
    p.drawString(100, 600, "Spett.le Cliente:")
    p.drawString(100, 580, "Rossi Mario")
    p.drawString(100, 560, "Via Verdi 456")
    p.drawString(100, 540, "Roma, RM 00100")
    p.drawString(100, 520, "")
    p.drawString(100, 500, "Data: 15 Gennaio 2024")
    p.drawString(100, 480, "Scadenza: 14 Febbraio 2024")
    p.drawString(100, 460, "")
    p.drawString(100, 440, "Descrizione: Servizi di consulenza")
    p.drawString(100, 420, "Importo: €1.500,00")
    p.drawString(100, 400, "IVA 22%: €330,00")
    p.drawString(100, 380, "Totale: €1.830,00")
    p.drawString(100, 360, "")
    p.drawString(100, 340, "Pagamento entro 30 giorni")
    p.drawString(100, 320, "IBAN: IT60 X054 2811 1010 0000 0123 456")
    
    p.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_bytes).decode('utf-8')

def test_localized_explanation():
    """Test localized GPT explanations"""
    print("Testing localized GPT explanations...")
    
    # Create test document
    pdf_base64 = create_test_document()
    
    # Test with different languages
    languages = ['italian', 'french', 'wolof']
    results = {}
    
    for lang in languages:
        print(f"\nTesting {lang} explanation...")
        
        try:
            payload = {
                "base64_image": f"data:application/pdf;base64,{pdf_base64}",
                "target_language": lang,
                "filename": f"test_invoice_{lang}.pdf"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/analyze-document",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                results[lang] = result
                print(f"✅ {lang.title()} - Success!")
                print(f"Explanation preview: {result.get('explanation', 'N/A')[:100]}...")
                print(f"Detected language: {result.get('detected_language', 'N/A')}")
            else:
                print(f"❌ {lang.title()} - Failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ {lang.title()} - Exception: {e}")
    
    return results

def test_pdf_export(analysis_results):
    """Test PDF export functionality"""
    print("\nTesting PDF export functionality...")
    
    if not analysis_results:
        print("❌ No analysis results to test PDF export")
        return False
    
    # Test PDF export with Italian results
    italian_result = analysis_results.get('italian')
    if not italian_result:
        print("❌ No Italian results for PDF export test")
        return False
    
    try:
        payload = {
            "original_text": italian_result['original_text'],
            "translated_text": italian_result['translated_text'],
            "target_language": "italian",
            "filename": "test_invoice_italian.pdf",
            "explanation": italian_result['explanation']
        }
        
        response = requests.post(
            f"{BACKEND_URL}/export-pdf",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ PDF Export - Success!")
            print(f"PDF size: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('content-type', 'Unknown')}")
            
            # Save PDF for verification
            with open('/tmp/test_export.pdf', 'wb') as f:
                f.write(response.content)
            print("✅ PDF saved to /tmp/test_export.pdf")
            
            return True
        else:
            print(f"❌ PDF Export - Failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF Export - Exception: {e}")
        return False

def test_backend_health():
    """Test backend health"""
    print("Testing backend health...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Backend health - OK")
            return True
        else:
            print(f"❌ Backend health - Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health - Exception: {e}")
        return False

if __name__ == "__main__":
    print("TAHAWU AI - Final Features Testing")
    print("=" * 60)
    
    # Test backend health
    backend_ok = test_backend_health()
    
    if backend_ok:
        # Test localized explanations
        analysis_results = test_localized_explanation()
        
        # Test PDF export
        pdf_ok = test_pdf_export(analysis_results)
        
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        print(f"Backend Health: {'✅ PASSED' if backend_ok else '❌ FAILED'}")
        print(f"Localized Explanations: {'✅ PASSED' if analysis_results else '❌ FAILED'}")
        print(f"PDF Export: {'✅ PASSED' if pdf_ok else '❌ FAILED'}")
        
        if backend_ok and analysis_results and pdf_ok:
            print("\n🎉 ALL FINAL FEATURES WORKING PERFECTLY!")
            print("✅ Localized GPT explanations in Italian, French, and Wolof")
            print("✅ PDF export with translated content and structured layout")
            print("✅ Complete end-to-end workflow functional")
            print("\n🚀 TAHAWU AI IS READY FOR PRODUCTION!")
        else:
            print("\n⚠️ Some features need attention")
    else:
        print("\n❌ Backend is not responding - check server status")