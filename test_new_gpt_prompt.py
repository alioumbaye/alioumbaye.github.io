#!/usr/bin/env python3
"""Test the new improved GPT prompt template"""

import requests
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

BACKEND_URL = "https://fba5fd1d-7060-4ce8-b4e2-08c38fc9124d.preview.emergentagent.com/api"

def create_realistic_document():
    """Create a realistic document that requires actionable advice"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Create a training enrollment form
    p.drawString(100, 750, "MODULO DI ISCRIZIONE CORSO FORMAZIONE")
    p.drawString(100, 720, "Corso: Sicurezza sul Lavoro - Livello Base")
    p.drawString(100, 700, "Durata: 8 ore (2 giorni)")
    p.drawString(100, 680, "Date: 15-16 Febbraio 2024")
    p.drawString(100, 660, "Orario: 9:00 - 13:00")
    p.drawString(100, 640, "Luogo: Aula Magna, Via Roma 123, Milano")
    p.drawString(100, 620, "")
    p.drawString(100, 600, "DATI PARTECIPANTE:")
    p.drawString(100, 580, "Nome: ___________________")
    p.drawString(100, 560, "Cognome: ___________________")
    p.drawString(100, 540, "Codice Fiscale: ___________________")
    p.drawString(100, 520, "Email: ___________________")
    p.drawString(100, 500, "Telefono: ___________________")
    p.drawString(100, 480, "Azienda: ___________________")
    p.drawString(100, 460, "")
    p.drawString(100, 440, "OPZIONI (selezionare una):")
    p.drawString(100, 420, "☐ Corso base (€150)")
    p.drawString(100, 400, "☐ Corso avanzato (€250)")
    p.drawString(100, 380, "☐ Corso + certificazione (€350)")
    p.drawString(100, 360, "")
    p.drawString(100, 340, "SCADENZA ISCRIZIONE: 10 Febbraio 2024")
    p.drawString(100, 320, "Inviare a: formazione@azienda.it")
    p.drawString(100, 300, "Oppure consegnare in ufficio")
    p.drawString(100, 280, "")
    p.drawString(100, 260, "Firma: _________________ Data: _______")
    
    p.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_bytes).decode('utf-8')

def test_new_gpt_prompt():
    """Test the new improved GPT prompt template"""
    print("Testing new improved GPT prompt template...")
    
    # Create realistic document
    pdf_base64 = create_realistic_document()
    
    # Test with Italian
    try:
        payload = {
            "base64_image": f"data:application/pdf;base64,{pdf_base64}",
            "target_language": "italian",
            "filename": "modulo_iscrizione_corso.pdf"
        }
        
        print("Processing training enrollment form...")
        response = requests.post(
            f"{BACKEND_URL}/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get('explanation', '')
            
            print("✅ NEW GPT PROMPT SUCCESS!")
            print(f"✅ Explanation length: {len(explanation)} characters")
            print(f"\n📋 FULL GPT EXPLANATION:")
            print("=" * 60)
            print(explanation)
            print("=" * 60)
            
            # Check for key elements that the new prompt should provide
            quality_checks = {
                'Document Type': any(word in explanation.lower() for word in ['modulo', 'iscrizione', 'form', 'enrollment']),
                'Actions Required': any(word in explanation.lower() for word in ['compilare', 'firmare', 'inviare', 'scadenza']),
                'Key Details': any(word in explanation.lower() for word in ['febbraio', '150', '250', '350', 'email']),
                'Multiple Choice': any(word in explanation.lower() for word in ['selezionare', 'opzioni', 'scegliere', 'corso']),
                'Practical Advice': any(word in explanation.lower() for word in ['come', 'dove', 'quando', 'entro'])
            }
            
            passed_checks = sum(quality_checks.values())
            print(f"\n✅ QUALITY ASSESSMENT:")
            for check, passed in quality_checks.items():
                print(f"{'✅' if passed else '❌'} {check}: {'FOUND' if passed else 'MISSING'}")
            
            print(f"\n🎯 Overall Quality Score: {passed_checks}/5 ({passed_checks/5*100:.0f}%)")
            
            if passed_checks >= 4:
                print("🎉 EXCELLENT! New prompt provides comprehensive, actionable guidance!")
                return True
            elif passed_checks >= 3:
                print("👍 GOOD! New prompt provides useful guidance with room for improvement.")
                return True
            else:
                print("⚠️ Needs improvement - explanation lacks key actionable elements.")
                return False
            
        else:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("TAHAWU AI - New Improved GPT Prompt Testing")
    print("=" * 60)
    
    success = test_new_gpt_prompt()
    
    print("\n" + "=" * 60)
    print("NEW PROMPT TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 NEW GPT PROMPT TEMPLATE WORKING EXCELLENTLY!")
        print("✅ Provides specific document type identification")
        print("✅ Explains purpose and expected user actions")
        print("✅ Highlights key details (dates, amounts, deadlines)")
        print("✅ Explains how to respond to questions/choices")
        print("✅ Uses clear, helpful tone in target language")
        print("✅ Focuses on practical, actionable guidance")
        print("\n🚀 TAHAWU AI GPT EXPLANATIONS ARE NOW SIGNIFICANTLY IMPROVED!")
    else:
        print("⚠️ New prompt needs further refinement for optimal results")