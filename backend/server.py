from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
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

# Helper functions
def extract_text_from_image(base64_image: str) -> str:
    """Extract text from image using Google Cloud Vision API"""
    try:
        # Remove data URL prefix if present
        if 'base64,' in base64_image:
            base64_image = base64_image.split('base64,')[1]
        
        # Validate base64 string
        try:
            base64.b64decode(base64_image)
        except Exception:
            raise Exception("Invalid base64 image data")
        
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
                    ]
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Vision API HTTP error {response.status_code}: {response.text}")
        
        result = response.json()
        
        # Check for API errors in response
        if 'responses' in result and len(result['responses']) > 0:
            resp = result['responses'][0]
            
            # Check for errors in the response
            if 'error' in resp:
                raise Exception(f"Vision API error: {resp['error']}")
            
            if 'textAnnotations' in resp and len(resp['textAnnotations']) > 0:
                return resp['textAnnotations'][0]['description']
        
        return ""
        
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")

def generate_document_explanation(original_text: str, translated_text: str, target_language: str) -> str:
    """Generate explanation using OpenAI GPT"""
    try:
        import openai
        
        # Set up OpenAI client (you'll need to add API key to .env)
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        if not openai.api_key:
            # Fallback explanation if no OpenAI key
            return f"This document contains text that has been translated from the original language to {target_language}. The document appears to contain information that may require your attention or action."
        
        prompt = f"""
        You are a helpful assistant that explains documents in simple terms.
        
        Original text: {original_text}
        Translated text ({target_language}): {translated_text}
        
        Please provide a clear, simple explanation of:
        1. What type of document this appears to be
        2. The main purpose or content of the document
        3. Any important actions the reader should take
        
        Keep the explanation concise but helpful. Write in English.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains documents clearly and concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logging.warning(f"GPT explanation failed: {e}")
        # Fallback explanation
        return f"This document contains text that has been successfully translated to {target_language}. Based on the content, it appears to be a document that may contain important information for your review."

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