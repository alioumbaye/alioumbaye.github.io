from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
import json
import requests
from urllib.parse import quote
import io
from pdf2image import convert_from_bytes
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Google Cloud API Key
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class DocumentAnalysisRequest(BaseModel):
    base64_image: str
    target_language: str
    filename: Optional[str] = "document"

class DocumentAnalysisResponse(BaseModel):
    success: bool
    original_text: str
    translated_text: str
    explanation: str
    detected_language: str
    target_language: str
    timestamp: datetime

class TranslationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str
    translated_text: str
    detected_language: str
    target_language: str
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PDFExportRequest(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    filename: str
    explanation: str

def generate_translated_pdf(original_text: str, translated_text: str, target_language: str, filename: str, explanation: str) -> bytes:
    """Generate a PDF with the translated text maintaining structure"""
    try:
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#667eea'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#333333'),
            leftIndent=0
        )
        
        body_style = ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14,
            leftIndent=0
        )
        
        # Language names for title
        language_names = {
            'italian': 'Italiano',
            'french': 'Français',
            'wolof': 'Wolof'
        }
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(f"TAHAWU AI - Documento Tradotto", title_style))
        story.append(Paragraph(f"Traduzione in {language_names.get(target_language, target_language.title())}", heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Document info
        story.append(Paragraph(f"<b>File originale:</b> {filename}", body_style))
        story.append(Paragraph(f"<b>Lingua di destinazione:</b> {language_names.get(target_language, target_language.title())}", body_style))
        story.append(Paragraph(f"<b>Data di elaborazione:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Translated text sections
        story.append(Paragraph("Testo Tradotto", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Parse and format translated text
        sections = translated_text.split('\n\n')
        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Check if it's a page header or section header
                        if line.startswith('--- ') or line.upper() == line and len(line) < 50:
                            story.append(Paragraph(f"<b>{line}</b>", heading_style))
                        else:
                            story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Add explanation section
        story.append(PageBreak())
        story.append(Paragraph("Spiegazione del Documento", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Format explanation
        explanation_paragraphs = explanation.split('\n')
        for para in explanation_paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), body_style))
        
        # Build PDF
        doc.build(story)
        
        # Return PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

# Helper functions (existing functions remain the same)...
def is_pdf_file(base64_data: str) -> bool:
    """Check if the base64 data represents a PDF file"""
    try:
        # Remove data URL prefix if present
        if 'base64,' in base64_data:
            base64_data = base64_data.split('base64,')[1]
        
        # Decode base64 to bytes
        file_bytes = base64.b64decode(base64_data)
        
        # Check PDF magic bytes
        return file_bytes.startswith(b'%PDF')
    except Exception:
        return False

def convert_pdf_to_images(pdf_bytes: bytes) -> List[str]:
    """Convert PDF bytes to list of base64 image strings with improved error handling"""
    try:
        # Convert PDF to PIL images with higher DPI for better OCR
        images = convert_from_bytes(
            pdf_bytes, 
            dpi=400,  # Higher DPI for better text recognition
            fmt='png',
            thread_count=2,  # Use multiple threads
            poppler_path=None,
            first_page=None,
            last_page=None,
            use_cropbox=False,
            strict=False  # Be more lenient with PDF parsing
        )
        
        if not images:
            raise Exception("No pages could be extracted from PDF")
        
        base64_images = []
        for page_num, image in enumerate(images):
            try:
                # Optimize image for OCR
                # Convert to RGB if not already
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Enhance image contrast for better OCR
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.2)  # Slight contrast boost
                
                # Convert PIL image to base64
                buffer = io.BytesIO()
                image.save(buffer, format='PNG', optimize=True, quality=95)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                base64_images.append(img_base64)
                
                logging.info(f"Successfully processed PDF page {page_num + 1}")
                
            except Exception as page_error:
                logging.warning(f"Failed to process PDF page {page_num + 1}: {page_error}")
                continue
        
        if not base64_images:
            raise Exception("No pages could be successfully processed")
            
        logging.info(f"Successfully converted PDF to {len(base64_images)} images")
        return base64_images
        
    except Exception as e:
        raise Exception(f"PDF conversion failed: {str(e)}")

def extract_text_from_single_image(base64_image: str, page_num: int = 1) -> str:
    """Extract text from a single image using Google Cloud Vision API with better error handling"""
    try:
        # Use standard Google Cloud Vision API with API key
        url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": base64_image
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": 50
                        }
                    ],
                    "imageContext": {
                        "languageHints": ["it", "fr", "en", "es", "de"]  # Common languages
                    }
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        
        if response.status_code != 200:
            raise Exception(f"Vision API HTTP error {response.status_code}: {response.text}")
        
        result = response.json()
        
        # Check for API errors in response
        if 'responses' in result and len(result['responses']) > 0:
            resp = result['responses'][0]
            
            # Check for errors in the response
            if 'error' in resp:
                raise Exception(f"Vision API error for page {page_num}: {resp['error']}")
            
            if 'textAnnotations' in resp and len(resp['textAnnotations']) > 0:
                extracted_text = resp['textAnnotations'][0]['description']
                logging.info(f"Extracted {len(extracted_text)} characters from page {page_num}")
                return extracted_text
        
        logging.warning(f"No text found in page {page_num}")
        return ""
        
    except Exception as e:
        raise Exception(f"Text extraction failed for page {page_num}: {str(e)}")

def extract_text_from_image(base64_image: str) -> str:
    """Extract text from image or PDF using Google Cloud Vision API with improved processing"""
    try:
        # Remove data URL prefix if present
        if 'base64,' in base64_image:
            base64_data = base64_image.split('base64,')[1]
        else:
            base64_data = base64_image
        
        # Validate base64 string
        try:
            file_bytes = base64.b64decode(base64_data)
        except Exception:
            raise Exception("Invalid base64 image data")
        
        # Check if it's a PDF file
        if is_pdf_file(base64_image):
            logging.info("Processing PDF file with improved handling...")
            
            try:
                # Convert PDF to images
                pdf_images = convert_pdf_to_images(file_bytes)
                
                if not pdf_images:
                    raise Exception("Could not convert PDF to images")
                
                # Extract text from each page with retry logic
                all_text = []
                successful_pages = 0
                
                for i, img_base64 in enumerate(pdf_images):
                    max_retries = 2
                    page_text = ""
                    
                    for retry in range(max_retries):
                        try:
                            page_text = extract_text_from_single_image(img_base64, i + 1)
                            successful_pages += 1
                            break
                        except Exception as e:
                            logging.warning(f"Attempt {retry + 1} failed for page {i+1}: {e}")
                            if retry == max_retries - 1:
                                logging.error(f"Failed to extract text from page {i+1} after {max_retries} attempts")
                            else:
                                import time
                                time.sleep(1)  # Brief pause before retry
                
                    if page_text and page_text.strip():
                        all_text.append(f"--- Pagina {i+1} ---\n{page_text.strip()}")
                
                if not all_text:
                    raise Exception(f"No text could be extracted from any of the {len(pdf_images)} PDF pages")
                
                final_text = "\n\n".join(all_text)
                logging.info(f"Successfully extracted text from {successful_pages}/{len(pdf_images)} pages")
                logging.info(f"Total extracted text length: {len(final_text)} characters")
                
                return final_text
                
            except Exception as pdf_error:
                logging.error(f"PDF processing failed: {pdf_error}")
                raise Exception(f"PDF processing failed: {str(pdf_error)}")
        
        else:
            # Handle as regular image
            logging.info("Processing image file...")
            return extract_text_from_single_image(base64_data)
        
    except Exception as e:
        logging.error(f"Document processing failed: {e}")
        raise Exception(f"Text extraction failed: {str(e)}")

def generate_document_explanation(original_text: str, translated_text: str, target_language: str) -> str:
    """Generate detailed, context-aware explanation using improved GPT prompt template"""
    try:
        # Check if OpenAI API key is available
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if not openai_api_key or openai_api_key == 'sk-placeholder-key':
            # Enhanced fallback explanations based on target language
            return get_enhanced_fallback_explanation(original_text, translated_text, target_language)
        
        try:
            # Use the new OpenAI client format
            from openai import OpenAI
            
            client = OpenAI(api_key=openai_api_key)
            
            # Language mapping for the improved prompt template
            language_names = {
                'italian': 'italiano',
                'french': 'français', 
                'wolof': 'wolof'
            }
            
            selected_language = language_names.get(target_language, target_language)
            
            # Create the improved, more structured prompt
            system_prompt = f"""You are a multilingual assistant helping users understand official or technical documents. The user has uploaded a document translated to {selected_language}.

Your task is to:
1. Carefully read and analyze the content
2. Identify the type of document (questionnaire, letter, contract, training module, invoice, form, certificate, etc.)
3. Explain the purpose of the document and what the user is expected to do with it
4. Highlight key details (dates, names, actions, obligations, amounts, deadlines)
5. If the document includes questions or multiple-choice, explain how to respond
6. Write the explanation in {selected_language}, using a clear and helpful tone

Important: Avoid repeating the full text. Instead, summarize and explain meaning and action points."""

            user_prompt = f"""Please analyze this document and provide a helpful explanation:

DOCUMENT CONTENT:
{translated_text[:2000]}

Please provide a clear, structured explanation in {selected_language} that helps the user understand:
- What type of document this is
- What they need to do with it
- Any important dates, deadlines, or actions required
- How to properly respond if it contains questions or forms

Focus on being practical and actionable rather than just descriptive."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=650,  # Increased for more comprehensive explanations
                temperature=0.2  # Lower for more consistent, focused responses
            )
            
            explanation = response.choices[0].message.content.strip()
            logging.info(f"Generated improved GPT explanation in {target_language}: {len(explanation)} characters")
            return explanation
            
        except Exception as openai_error:
            logging.warning(f"OpenAI API call failed: {openai_error}")
            return get_enhanced_fallback_explanation(original_text, translated_text, target_language)
        
    except Exception as e:
        logging.error(f"Document explanation generation failed: {e}")
        return get_enhanced_fallback_explanation(original_text, translated_text, target_language)

def get_enhanced_fallback_explanation(original_text: str, translated_text: str, target_language: str) -> str:
    """Generate enhanced fallback explanations using the improved template structure"""
    
    # Analyze document content for better context-aware explanations
    text_to_analyze = translated_text.lower()
    
    # Enhanced document type detection with more categories
    doc_type = "documento"
    doc_actions = ""
    key_details = []
    
    # More comprehensive document type detection
    if any(word in text_to_analyze for word in ["fattura", "invoice", "bill", "pagare", "importo", "totale", "iva"]):
        doc_type = "fattura" if target_language == 'italian' else "facture" if target_language == 'french' else "bili"
        doc_actions = "pagare entro la scadenza" if target_language == 'italian' else "payer avant l'échéance" if target_language == 'french' else "fey ci deadline bi"
        
    elif any(word in text_to_analyze for word in ["contratto", "contract", "accordo", "firmare", "stipulare"]):
        doc_type = "contratto" if target_language == 'italian' else "contrat" if target_language == 'french' else "kontara"
        doc_actions = "leggere, firmare e restituire" if target_language == 'italian' else "lire, signer et retourner" if target_language == 'french' else "jàng, siine te delloo"
        
    elif any(word in text_to_analyze for word in ["modulo", "form", "iscrizione", "compilare", "richiesta", "domanda"]):
        doc_type = "modulo di iscrizione" if target_language == 'italian' else "formulaire d'inscription" if target_language == 'french' else "formulaire bu bokk"
        doc_actions = "compilare tutti i campi e inviare" if target_language == 'italian' else "remplir tous les champs et envoyer" if target_language == 'french' else "fey lépp te yónnee"
        
    elif any(word in text_to_analyze for word in ["questionario", "questionnaire", "survey", "domande", "risposte"]):
        doc_type = "questionario" if target_language == 'italian' else "questionnaire" if target_language == 'french' else "laaj"
        doc_actions = "rispondere a tutte le domande" if target_language == 'italian' else "répondre à toutes les questions" if target_language == 'french' else "jàngal lépp laaj yi"
        
    elif any(word in text_to_analyze for word in ["certificato", "certificate", "attestato", "diploma"]):
        doc_type = "certificato" if target_language == 'italian' else "certificat" if target_language == 'french' else "sertifika"
        doc_actions = "conservare per i propri archivi" if target_language == 'italian' else "conserver pour vos archives" if target_language == 'french' else "moytul ci sa file yi"
        
    elif any(word in text_to_analyze for word in ["lettera", "letter", "comunicazione", "avviso", "notifica"]):
        doc_type = "lettera ufficiale" if target_language == 'italian' else "lettre officielle" if target_language == 'french' else "bataaxal bu ofisiyel"
        doc_actions = "leggere attentamente e seguire le istruzioni" if target_language == 'italian' else "lire attentivement et suivre les instructions" if target_language == 'french' else "jàng bu baax te topale njàng yi"
    
    # Extract key details from the text
    import re
    
    # Find dates
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{1,2}\s+\w+\s+\d{2,4}',
        r'\w+\s+\d{1,2},?\s+\d{2,4}'
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, translated_text, re.IGNORECASE)
        key_details.extend(dates[:3])  # Limit to first 3 dates
    
    # Find monetary amounts
    money_patterns = [
        r'€\s*\d+[.,]?\d*',
        r'\d+[.,]?\d*\s*€',
        r'\d+[.,]?\d*\s*euro'
    ]
    for pattern in money_patterns:
        amounts = re.findall(pattern, translated_text, re.IGNORECASE)
        key_details.extend(amounts[:3])  # Limit to first 3 amounts
    
    # Find emails and phones
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'[\+]?[\d\s\-\(\)]{8,15}'
    
    emails = re.findall(email_pattern, translated_text)
    phones = re.findall(phone_pattern, translated_text)
    
    key_details.extend(emails[:2])
    key_details.extend(phones[:2])
    
    # Generate structured explanation based on target language
    if target_language == 'italian':
        explanation = f"""**ANALISI DEL DOCUMENTO**

**1. TIPO DI DOCUMENTO:** 
Questo è un {doc_type} che è stato tradotto automaticamente in italiano.

**2. SCOPO E FUNZIONE:** 
Il documento contiene informazioni ufficiali che richiedono la vostra attenzione e possibili azioni da parte vostra.

**3. COSA DOVETE FARE:** 
{doc_actions if doc_actions else "Leggete attentamente tutto il contenuto e identificate eventuali azioni richieste"}

**4. INFORMAZIONI CHIAVE DA NOTARE:**"""

        if key_details:
            explanation += f"""
{chr(10).join([f"• {detail}" for detail in key_details[:5]])}"""
        else:
            explanation += """
• Date e scadenze menzionate nel documento
• Importi o numeri di riferimento
• Contatti per informazioni aggiuntive"""

        explanation += f"""

**5. COME RISPONDERE:**
Se il documento contiene domande o scelte multiple, selezionate la risposta più appropriata per la vostra situazione.

**6. PROSSIMI PASSI:**
• Verificate se ci sono scadenze da rispettare
• Preparate eventuali documenti richiesti
• Contattate gli uffici competenti se avete dubbi
• Conservate una copia per i vostri archivi

**IMPORTANTE:** Verificate sempre le informazioni critiche con la fonte originale se necessario."""

    elif target_language == 'french':
        explanation = f"""**ANALYSE DU DOCUMENT**

**1. TYPE DE DOCUMENT:** 
Ceci est un {doc_type} qui a été traduit automatiquement en français.

**2. OBJECTIF ET FONCTION:** 
Le document contient des informations officielles qui nécessitent votre attention et possibles actions de votre part.

**3. CE QUE VOUS DEVEZ FAIRE:** 
{doc_actions if doc_actions else "Lisez attentivement tout le contenu et identifiez les actions requises éventuelles"}

**4. INFORMATIONS CLÉS À NOTER:**"""

        if key_details:
            explanation += f"""
{chr(10).join([f"• {detail}" for detail in key_details[:5]])}"""
        else:
            explanation += """
• Dates et échéances mentionnées dans le document
• Montants ou numéros de référence
• Contacts pour informations supplémentaires"""

        explanation += f"""

**5. COMMENT RÉPONDRE:**
Si le document contient des questions ou choix multiples, sélectionnez la réponse la plus appropriée pour votre situation.

**6. PROCHAINES ÉTAPES:**
• Vérifiez s'il y a des échéances à respecter
• Préparez les documents éventuellement requis
• Contactez les bureaux compétents si vous avez des doutes
• Conservez une copie pour vos archives

**IMPORTANT:** Vérifiez toujours les informations critiques avec la source originale si nécessaire."""

    elif target_language == 'wolof':
        explanation = f"""**XOOLAL DOKIMAA BI**

**1. NDAM DOKIMAA:** 
Loolu {doc_type} la bu tektal otomatik ci wolof.

**2. JARIÑ AK LIGGÉEY:** 
Dokimaa bii am na jagleel yu ofisiyel yu laaj sa xol ak liggéey yu nga mën a def.

**3. LOOLU NGA WAR A DEF:** 
{doc_actions if doc_actions else "Jàng lépp loolu ci biir te gis su am loolu la war a def"}

**4. JAGLEEL YU GËSTU:**"""

        if key_details:
            explanation += f"""
{chr(10).join([f"• {detail}" for detail in key_details[:5]])}"""
        else:
            explanation += """
• Bis ak deadline yu toj ci dokimaa bi
• Xaalis walla nimero yu reference
• Contact ngir am jagleel yu dul"""

        explanation += f"""

**5. Na NGA JÀNGAL:**
Su dokimaa bii am laaj walla choix multiple, taan loolu lu gën a moo ngi ci sa xeetu.

**6. TÀNN YU JËKK:**
• Xool bu am deadline yu war a topale
• Samp dokimaa yu laajee
• Jàngal bureau yu gëm su am jafe
• Moytul benn copy ci sa file

**GËSTU:** Xoolal lépp jagleel yu gëstu ak source bu njëkk su soxla."""

    else:
        explanation = f"This {doc_type} has been automatically translated to {target_language}. The document contains official information that requires your attention and may need specific actions from you. Please read carefully and identify any required actions, important dates, amounts, or contact information. If the document contains questions or multiple choices, select the most appropriate response for your situation."

    return explanation

def translate_text(text: str, target_language: str) -> dict:
    """Translate text using Google Translate API"""
    try:
        # Language code mapping
        lang_mapping = {
            'italian': 'it',
            'french': 'fr',
            'wolof': 'wo'
        }
        
        target_lang_code = lang_mapping.get(target_language.lower(), target_language)
        
        url = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}"
        
        payload = {
            'q': text,
            'target': target_lang_code,
            'format': 'text'
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Translation API error: {response.text}")
        
        result = response.json()
        
        if 'data' in result and 'translations' in result['data']:
            translation = result['data']['translations'][0]
            return {
                'translated_text': translation['translatedText'],
                'detected_language': translation.get('detectedSourceLanguage', 'unknown')
            }
        
        raise Exception("No translation found in response")
        
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

@api_router.post("/export-pdf")
async def export_translated_pdf(request: PDFExportRequest):
    try:
        # Generate PDF with translated content
        pdf_bytes = generate_translated_pdf(
            request.original_text,
            request.translated_text,
            request.target_language,
            request.filename,
            request.explanation
        )
        
        # Create filename for download
        base_name = os.path.splitext(request.filename)[0]
        language_suffix = {
            'italian': 'IT',
            'french': 'FR',
            'wolof': 'WO'
        }.get(request.target_language, request.target_language.upper())
        
        download_filename = f"{base_name}_translated_{language_suffix}.pdf"
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "TAHAWU AI - Document Translation API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest):
    try:
        # Extract text from image using Google Cloud Vision
        extracted_text = extract_text_from_image(request.base64_image)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text found in the uploaded image")
        
        # Translate the extracted text
        translation_result = translate_text(extracted_text, request.target_language)
        
        # Generate GPT explanation
        explanation = generate_document_explanation(
            extracted_text, 
            translation_result['translated_text'], 
            request.target_language
        )
        
        # Create response
        response_data = DocumentAnalysisResponse(
            success=True,
            original_text=extracted_text,
            translated_text=translation_result['translated_text'],
            explanation=explanation,
            detected_language=translation_result['detected_language'],
            target_language=request.target_language,
            timestamp=datetime.utcnow()
        )
        
        # Save to database
        translation_history = TranslationHistory(
            original_text=extracted_text,
            translated_text=translation_result['translated_text'],
            detected_language=translation_result['detected_language'],
            target_language=request.target_language,
            filename=request.filename
        )
        
        await db.translation_history.insert_one(translation_history.dict())
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/translation-history", response_model=List[TranslationHistory])
async def get_translation_history():
    try:
        history = await db.translation_history.find().sort("timestamp", -1).to_list(50)
        return [TranslationHistory(**item) for item in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/translate-text")
async def translate_text_only(text: str = Form(...), target_language: str = Form(...)):
    try:
        translation_result = translate_text(text, target_language)
        return {
            "success": True,
            "original_text": text,
            "translated_text": translation_result['translated_text'],
            "detected_language": translation_result['detected_language'],
            "target_language": target_language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()