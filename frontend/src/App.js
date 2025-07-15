import React, { useState, useRef } from "react";
import { useTranslation } from 'react-i18next';
import "./App.css";
import "./i18n";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const { t, i18n } = useTranslation();
  const [uiLanguage, setUiLanguage] = useState('it');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('tabs'); // 'tabs', 'sideBySide', 'sections'
  const fileInputRef = useRef(null);

  const uiLanguages = [
    { code: 'it', name: 'Italiano', flag: '🇮🇹' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'wo', name: 'Wolof', flag: '🌍' }
  ];

  const languages = [
    { code: 'italian', name: t('italian'), flag: '🇮🇹' },
    { code: 'french', name: t('french'), flag: '🇫🇷' },
    { code: 'wolof', name: t('wolof'), flag: '🇸🇳' }
  ];

  const handleUILanguageChange = (langCode) => {
    setUiLanguage(langCode);
    i18n.changeLanguage(langCode);
  };

  const handleLanguageSelect = (language) => {
    setSelectedLanguage(language);
    setError('');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      setError(t('invalidFileType'));
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      setError(t('fileTooLarge'));
      return;
    }

    setUploadedFile(file);
    setError('');
    setResult(null);

    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      setImagePreview(null);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const handleAnalyzeDocument = async () => {
    if (!selectedLanguage) {
      setError(t('selectLanguageFirst'));
      return;
    }

    if (!uploadedFile) {
      setError(t('uploadDocumentFirst'));
      return;
    }

    setAnalyzing(true);
    setError('');

    try {
      // Convert file to base64
      const base64Image = await fileToBase64(uploadedFile);
      
      const response = await axios.post(`${API}/analyze-document`, {
        base64_image: base64Image,
        target_language: selectedLanguage,
        filename: uploadedFile.name
      });

      setResult(response.data);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || t('analysisError');
      setError(errorMessage);
      console.error('Analysis error:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const resetApp = () => {
    setSelectedLanguage('');
    setUploadedFile(null);
    setImagePreview(null);
    setResult(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Helper function to detect section headers
  const detectSectionHeaders = (text) => {
    const lines = text.split('\n');
    const sections = [];
    let currentSection = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // Check for page headers
      if (line.startsWith('--- Page') || line.startsWith('--- Pagina') || line.startsWith('--- Xët')) {
        if (currentSection) {
          sections.push(currentSection);
        }
        currentSection = {
          title: line,
          content: []
        };
      } else {
        if (!currentSection) {
          currentSection = {
            title: t('introduction'),
            content: []
          };
        }
        currentSection.content.push(line);
      }
    }
    
    if (currentSection) {
      sections.push(currentSection);
    }
    
    return sections;
  };

  const renderTextSections = (text, isTranslated = false) => {
    const sections = detectSectionHeaders(text);
    
    return sections.map((section, index) => (
      <div key={index} className="text-section">
        <h4 className="section-header">{section.title}</h4>
        <div className="section-content">
          {section.content.map((line, lineIndex) => (
            <p key={lineIndex} className="section-line">{line}</p>
          ))}
        </div>
      </div>
    ));
  };

  return (
    <div className="App">
      {/* Header */}
      <div className="header">
        <h1 className="app-title">TAHAWU AI</h1>
        <p className="app-subtitle">Document Translation Made Easy</p>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {!result ? (
          <>
            {/* Language Selection */}
            <div className="section">
              <h2 className="section-title">Select Target Language</h2>
              <div className="language-buttons">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    className={`language-btn ${selectedLanguage === lang.code ? 'selected' : ''}`}
                    onClick={() => handleLanguageSelect(lang.code)}
                  >
                    <span className="flag">{lang.flag}</span>
                    <span className="lang-name">{lang.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* File Upload */}
            <div className="section">
              <h2 className="section-title">Upload Document</h2>
              <div className="upload-container">
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={handleFileUpload}
                  className="file-input"
                  ref={fileInputRef}
                />
                <div className="upload-area">
                  {imagePreview ? (
                    <img src={imagePreview} alt="Preview" className="image-preview" />
                  ) : (
                    <div className="upload-placeholder">
                      <div className="upload-icon">📄</div>
                      <p>Upload an image or PDF</p>
                      <p className="upload-hint">Supports JPEG, PNG, GIF, PDF (max 5MB)</p>
                    </div>
                  )}
                </div>
                {uploadedFile && (
                  <div className="file-info">
                    <p><strong>Selected:</strong> {uploadedFile.name}</p>
                    <p><strong>Size:</strong> {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* Analyze Button */}
            <div className="section">
              <button
                className="analyze-btn"
                onClick={handleAnalyzeDocument}
                disabled={!selectedLanguage || !uploadedFile || analyzing}
              >
                {analyzing ? (
                  <>
                    <span className="loading-spinner"></span>
                    Analyzing Document...
                  </>
                ) : (
                  'Analyze Document'
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
          </>
        ) : (
          /* Results */
          <div className="results-section">
            <div className="result-header">
              <h2>Translation Complete!</h2>
              <button className="reset-btn" onClick={resetApp}>
                Start New Translation
              </button>
            </div>

            <div className="result-content">
              <div className="result-card">
                <h3>Original Text ({result.detected_language?.toUpperCase() || 'Unknown'})</h3>
                <div className="text-content">
                  {result.original_text}
                </div>
              </div>

              <div className="translation-arrow">
                <div className="arrow">↓</div>
                <div className="arrow-label">Translated to {selectedLanguage}</div>
              </div>

              <div className="result-card translated">
                <h3>Translated Text</h3>
                <div className="text-content">
                  {result.translated_text}
                </div>
              </div>

              <div className="translation-arrow">
                <div className="arrow">↓</div>
                <div className="arrow-label">Document Analysis</div>
              </div>

              <div className="result-card explanation">
                <h3>Document Explanation</h3>
                <div className="text-content">
                  {result.explanation}
                </div>
              </div>

              <div className="result-meta">
                <p><strong>File:</strong> {uploadedFile?.name}</p>
                <p><strong>Detected Language:</strong> {result.detected_language?.toUpperCase() || 'Unknown'}</p>
                <p><strong>Target Language:</strong> {selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}</p>
                <p><strong>Processed:</strong> {new Date(result.timestamp).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;