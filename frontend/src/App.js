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
  const [activeTab, setActiveTab] = useState('original');
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

  const handleDownloadPDF = async () => {
    try {
      const response = await axios.post(`${API}/export-pdf`, {
        original_text: result.original_text,
        translated_text: result.translated_text,
        target_language: selectedLanguage,
        filename: uploadedFile.name,
        explanation: result.explanation
      }, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename
      const baseName = uploadedFile.name.split('.')[0];
      const languageSuffix = {
        'italian': 'IT',
        'french': 'FR',
        'wolof': 'WO'
      }[selectedLanguage] || selectedLanguage.toUpperCase();
      
      link.setAttribute('download', `${baseName}_translated_${languageSuffix}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('PDF download failed:', error);
      setError('Failed to generate PDF download');
    }
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
      {/* Header with UI Language Selector */}
      <div className="header">
        <div className="header-top">
          <div className="ui-language-selector">
            <span className="ui-lang-label">{t('uiLanguage')}:</span>
            <div className="ui-language-buttons">
              {uiLanguages.map((lang) => (
                <button
                  key={lang.code}
                  className={`ui-lang-btn ${uiLanguage === lang.code ? 'active' : ''}`}
                  onClick={() => handleUILanguageChange(lang.code)}
                >
                  <span className="flag">{lang.flag}</span>
                  <span className="lang-name">{lang.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <h1 className="app-title">{t('appTitle')}</h1>
        <p className="app-subtitle">{t('appSubtitle')}</p>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {!result ? (
          <>
            {/* Language Selection */}
            <div className="section">
              <h2 className="section-title">{t('selectLanguage')}</h2>
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
              <h2 className="section-title">{t('uploadDocument')}</h2>
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
                      <p>{t('uploadPlaceholder')}</p>
                      <p className="upload-hint">{t('uploadHint')}</p>
                    </div>
                  )}
                </div>
                {uploadedFile && (
                  <div className="file-info">
                    <p><strong>{t('selectedFile')}</strong> {uploadedFile.name}</p>
                    <p><strong>{t('fileSize')}</strong> {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
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
                    {t('analyzingDocument')}
                  </>
                ) : (
                  t('analyzeDocument')
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
              <h2>{t('translationComplete')}</h2>
              <button className="reset-btn" onClick={resetApp}>
                {t('startNewTranslation')}
              </button>
            </div>

            {/* View Mode Selector */}
            <div className="view-mode-selector">
              <span className="view-label">{t('viewOptions')}:</span>
              <div className="view-buttons">
                <button
                  className={`view-btn ${viewMode === 'tabs' ? 'active' : ''}`}
                  onClick={() => setViewMode('tabs')}
                >
                  {t('tabs')}
                </button>
                <button
                  className={`view-btn ${viewMode === 'sideBySide' ? 'active' : ''}`}
                  onClick={() => setViewMode('sideBySide')}
                >
                  {t('sideBySide')}
                </button>
                <button
                  className={`view-btn ${viewMode === 'sections' ? 'active' : ''}`}
                  onClick={() => setViewMode('sections')}
                >
                  {t('sections')}
                </button>
              </div>
            </div>

            {/* Results Display */}
            <div className={`result-content ${viewMode}`}>
              {viewMode === 'tabs' && (
                <div className="tabs-container">
                  <div className="tab-buttons">
                    <button 
                      className={`tab-btn ${activeTab === 'original' ? 'active' : ''}`}
                      onClick={() => setActiveTab('original')}
                    >
                      {t('originalText')}
                    </button>
                    <button 
                      className={`tab-btn ${activeTab === 'translated' ? 'active' : ''}`}
                      onClick={() => setActiveTab('translated')}
                    >
                      {t('translatedText')}
                    </button>
                    <button 
                      className={`tab-btn ${activeTab === 'explanation' ? 'active' : ''}`}
                      onClick={() => setActiveTab('explanation')}
                    >
                      {t('documentExplanation')}
                    </button>
                  </div>
                  <div className="tab-content">
                    {activeTab === 'original' && (
                      <div className="tab-pane active">
                        <div className="result-card">
                          <h3>{t('originalText')} ({result.detected_language?.toUpperCase() || 'Unknown'})</h3>
                          <div className="text-content-sectioned">
                            {renderTextSections(result.original_text)}
                          </div>
                        </div>
                      </div>
                    )}
                    {activeTab === 'translated' && (
                      <div className="tab-pane active">
                        <div className="result-card translated">
                          <h3>{t('translatedText')}</h3>
                          <div className="text-content-sectioned">
                            {renderTextSections(result.translated_text, true)}
                          </div>
                        </div>
                      </div>
                    )}
                    {activeTab === 'explanation' && (
                      <div className="tab-pane active">
                        <div className="result-card explanation">
                          <h3>{t('documentExplanation')}</h3>
                          <div className="text-content">
                            {result.explanation}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {viewMode === 'sideBySide' && (
                <div className="side-by-side-container">
                  <div className="side-column">
                    <div className="result-card">
                      <h3>{t('originalText')} ({result.detected_language?.toUpperCase() || 'Unknown'})</h3>
                      <div className="text-content-sectioned">
                        {renderTextSections(result.original_text)}
                      </div>
                    </div>
                  </div>
                  <div className="side-column">
                    <div className="result-card translated">
                      <h3>{t('translatedText')}</h3>
                      <div className="text-content-sectioned">
                        {renderTextSections(result.translated_text, true)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'sections' && (
                <div className="sections-container">
                  <div className="result-card">
                    <h3>{t('originalText')} ({result.detected_language?.toUpperCase() || 'Unknown'})</h3>
                    <div className="text-content-sectioned">
                      {renderTextSections(result.original_text)}
                    </div>
                  </div>

                  <div className="translation-arrow">
                    <div className="arrow">↓</div>
                    <div className="arrow-label">{t('translatedTo')} {selectedLanguage}</div>
                  </div>

                  <div className="result-card translated">
                    <h3>{t('translatedText')}</h3>
                    <div className="text-content-sectioned">
                      {renderTextSections(result.translated_text, true)}
                    </div>
                  </div>

                  <div className="translation-arrow">
                    <div className="arrow">↓</div>
                    <div className="arrow-label">{t('documentAnalysis')}</div>
                  </div>

                  <div className="result-card explanation">
                    <h3>{t('documentExplanation')}</h3>
                    <div className="text-content">
                      {result.explanation}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="result-meta">
              <p><strong>{t('fileName')}</strong> {uploadedFile?.name}</p>
              <p><strong>{t('detectedLanguage')}</strong> {result.detected_language?.toUpperCase() || 'Unknown'}</p>
              <p><strong>{t('targetLanguage')}</strong> {selectedLanguage.charAt(0).toUpperCase() + selectedLanguage.slice(1)}</p>
              <p><strong>{t('processedAt')}</strong> {new Date(result.timestamp).toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;