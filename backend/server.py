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
    """Generate detailed, context-aware explanation using OpenAI GPT in the target language"""
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
            
            # Create enhanced, context-aware prompts for each language
            language_prompts = {
                'italian': {
                    'system_prompt': '''Sei un esperto analista di documenti che aiuta le persone a comprendere documenti complessi in italiano. 
                    Fornisci spiegazioni dettagliate, pratiche e utili che aiutino le persone a capire esattamente cosa devono fare con il documento.''',
                    'user_prompt': f"""
                    Analizza attentamente questo documento e fornisci una spiegazione completa e dettagliata in italiano:

                    TESTO DEL DOCUMENTO:
                    {translated_text[:1500]}

                    Fornisci una spiegazione strutturata che risponda a queste domande in modo dettagliato:

                    1. **TIPO DI DOCUMENTO**: Che tipo di documento è esattamente? (es: fattura, contratto, modulo, certificato, etc.)

                    2. **SCOPO E FUNZIONE**: A cosa serve questo documento? Perché è stato creato?

                    3. **CHI DEVE USARLO**: Chi sono le persone che tipicamente ricevono, compilano o utilizzano questo documento?

                    4. **QUANDO SI USA**: In quali situazioni o momenti questo documento viene utilizzato?

                    5. **AZIONI RICHIESTE**: Cosa deve fare esattamente la persona che riceve questo documento? Ci sono scadenze? Deve firmare, pagare, rispondere, o compilare qualcosa?

                    6. **INFORMAZIONI IMPORTANTI**: Quali sono le informazioni più importanti da notare? Ci sono numeri, date, importi o dettagli critici?

                    7. **PROSSIMI PASSI**: Quali sono i passi successivi consigliati dopo aver letto questo documento?

                    Scrivi in modo chiaro, dettagliato e pratico. Usa un linguaggio accessibile ma professionale.
                    """
                },
                'french': {
                    'system_prompt': '''Vous êtes un expert analyste de documents qui aide les gens à comprendre des documents complexes en français. 
                    Fournissez des explications détaillées, pratiques et utiles qui aident les gens à comprendre exactement ce qu'ils doivent faire avec le document.''',
                    'user_prompt': f"""
                    Analysez attentivement ce document et fournissez une explication complète et détaillée en français:

                    TEXTE DU DOCUMENT:
                    {translated_text[:1500]}

                    Fournissez une explication structurée qui répond à ces questions de manière détaillée:

                    1. **TYPE DE DOCUMENT**: De quel type de document s'agit-il exactement? (ex: facture, contrat, formulaire, certificat, etc.)

                    2. **OBJECTIF ET FONCTION**: À quoi sert ce document? Pourquoi a-t-il été créé?

                    3. **QUI DOIT L'UTILISER**: Qui sont les personnes qui reçoivent, remplissent ou utilisent typiquement ce document?

                    4. **QUAND L'UTILISER**: Dans quelles situations ou moments ce document est-il utilisé?

                    5. **ACTIONS REQUISES**: Que doit faire exactement la personne qui reçoit ce document? Y a-t-il des échéances? Doit-elle signer, payer, répondre, ou remplir quelque chose?

                    6. **INFORMATIONS IMPORTANTES**: Quelles sont les informations les plus importantes à noter? Y a-t-il des numéros, dates, montants ou détails critiques?

                    7. **PROCHAINES ÉTAPES**: Quelles sont les étapes suivantes recommandées après avoir lu ce document?

                    Écrivez de manière claire, détaillée et pratique. Utilisez un langage accessible mais professionnel.
                    """
                },
                'wolof': {
                    'system_prompt': '''Yaw bokk naa ci xam-xam dokimaa yi ngir jëkkal nit ñi ci gëstu dokimaa yu gëstu ci wolof. 
                    Jox jagleel yu mat, yu jëfandikoo te yu mën a jëkkal nit ñi ci xam loolu lan la war a def ak dokimaa bii.''',
                    'user_prompt': f"""
                    Xoolal lépp dokimaa bii te jox jagleel bu mat ak bu gëstu ci wolof:

                    MBIND GU CI DOKIMAA:
                    {translated_text[:1500]}

                    Jox jagleel bu sotti bu jàngal lii yu mat:

                    1. **NDAM DOKIMAA**: Lan dokimaa la? (sax: bili, ndimbalante, formulaire, sertifika, etc.)

                    2. **JARIÑ AK LIGGÉEY**: Lan la dokimaa bii jëfandikoo? Kuy koy defal ak luy?

                    3. **KAN LA WAR A KO JËFANDIKOO**: Kan nit ñi ñuy ko ko am, koy fey walla koy jëfandikoo?

                    4. **KAÑU LA KO JËFANDIKOO**: Ci ban xeetu walla kañu la dokimaa bii ko jëfandikoo?

                    5. **LI LA WAR A DEF**: Lan la kenn ku ko am a war a def? Am na deadline? War na siine, fey, jàngal, walla fey?

                    6. **JAGLEEL YU GËSTU**: Yan jagleel yu gëstu ci biir? Am na nimero, bis, xaalis walla cistaaraan yu gëstu?

                    7. **LOOLU MU JËKKI**: Yan tànn yu ñu mooy jàngal bu ma jàng dokimaa bii?

                    Bind ci yoon bu mat, bu toll ak bu mën a jëfandikoo. Jëfandikoo làkk bu naan-naan waaye bu professionnel.
                    """
                }
            }
            
            # Get language-specific prompt
            lang_config = language_prompts.get(target_language, language_prompts['italian'])
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": lang_config['system_prompt']},
                    {"role": "user", "content": lang_config['user_prompt']}
                ],
                max_tokens=600,  # Increased for more detailed explanations
                temperature=0.3  # Lower temperature for more focused, consistent responses
            )
            
            explanation = response.choices[0].message.content.strip()
            logging.info(f"Generated GPT explanation in {target_language}: {len(explanation)} characters")
            return explanation
            
        except Exception as openai_error:
            logging.warning(f"OpenAI API call failed: {openai_error}")
            return get_enhanced_fallback_explanation(original_text, translated_text, target_language)
        
    except Exception as e:
        logging.error(f"Document explanation generation failed: {e}")
        return get_enhanced_fallback_explanation(original_text, translated_text, target_language)

def get_enhanced_fallback_explanation(original_text: str, translated_text: str, target_language: str) -> str:
    """Generate enhanced fallback explanations with basic document analysis"""
    
    # Analyze document content for better fallback
    text_to_analyze = translated_text.lower()
    
    # Detect document type based on keywords
    doc_type = "documento"
    if any(word in text_to_analyze for word in ["fattura", "invoice", "bill", "pagare", "importo", "totale"]):
        doc_type = "fattura" if target_language == 'italian' else "facture" if target_language == 'french' else "bili"
    elif any(word in text_to_analyze for word in ["contratto", "contract", "accordo", "firmare", "stipulare"]):
        doc_type = "contratto" if target_language == 'italian' else "contrat" if target_language == 'french' else "kontara"
    elif any(word in text_to_analyze for word in ["modulo", "form", "compilare", "richiesta"]):
        doc_type = "modulo" if target_language == 'italian' else "formulaire" if target_language == 'french' else "formulaire"
    elif any(word in text_to_analyze for word in ["certificato", "certificate", "attestato"]):
        doc_type = "certificato" if target_language == 'italian' else "certificat" if target_language == 'french' else "sertifika"
    
    if target_language == 'italian':
        return f"""**ANALISI DEL DOCUMENTO**

**Tipo di Documento**: Questo è un {doc_type} che è stato tradotto in italiano usando l'intelligenza artificiale.

**Scopo**: Il documento contiene informazioni importanti che richiedono la vostra attenzione. Sembra essere un documento ufficiale o commerciale.

**Cosa Fare**: 
- Leggete attentamente tutto il contenuto tradotto
- Verificate le date, numeri e informazioni importanti
- Se contiene richieste o scadenze, prendete nota
- Se necessario, consultate un esperto per azioni specifiche

**Informazioni Importanti**: Il documento originale è stato estratto e tradotto automaticamente. Verificate sempre le informazioni critiche con la fonte originale se necessario.

**Prossimi Passi**: Analizzate il contenuto tradotto e decidete se sono necessarie azioni immediate o se dovete consultare qualcuno per ulteriori chiarimenti."""

    elif target_language == 'french':
        return f"""**ANALYSE DU DOCUMENT**

**Type de Document**: Ceci est un {doc_type} qui a été traduit en français en utilisant l'intelligence artificielle.

**Objectif**: Le document contient des informations importantes qui nécessitent votre attention. Il semble être un document officiel ou commercial.

**Que Faire**: 
- Lisez attentivement tout le contenu traduit
- Vérifiez les dates, numéros et informations importantes
- S'il contient des demandes ou échéances, prenez note
- Si nécessaire, consultez un expert pour des actions spécifiques

**Informations Importantes**: Le document original a été extrait et traduit automatiquement. Vérifiez toujours les informations critiques avec la source originale si nécessaire.

**Prochaines Étapes**: Analysez le contenu traduit et décidez si des actions immédiates sont nécessaires ou si vous devez consulter quelqu'un pour des clarifications supplémentaires."""

    elif target_language == 'wolof':
        return f"""**XOOLAL DOKIMAA BI**

**Ndam Dokimaa**: Loolu {doc_type} la bu tektal ci wolof ak AI.

**Jariñ**: Dokimaa bii am na jagleel yu gëstu yu mën a laaj sa xol. Mel na dokimaa bu ofiisiyel walla bu commerce.

**Loolu Nga War a Def**: 
- Jàng lépp mbind bu tektal bi
- Xool bis yi, nimero yi ak jagleel yu gëstu
- Su am laaj walla deadline, bind ko
- Su soxla, jàngal expert ngir liggéey yu bari

**Jagleel Yu Gëstu**: Dokimaa bu njëkk bi tektal na ak jëfandikoo otomatik. Xolaleen lépp jagleel yu gëstu ak kenn ku am dokimaa bu njëkk su soxla.

**Loolu Mu Jëkki**: Xoolal mbind bu tektal bi te décider su war nga def loolu bu bari walla war nga jàngal kenn ngir gën a xam.**"""

    else:
        return f"This {doc_type} has been translated to {target_language} using artificial intelligence. The document appears to contain important information that requires your attention and may need specific actions from you."

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