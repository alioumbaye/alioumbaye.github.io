import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  it: {
    translation: {
      // App Title and Header
      appTitle: "TAHAWU AI",
      appSubtitle: "Traduzione Documenti Semplificata",
      
      // Language Selection
      selectLanguage: "Seleziona Lingua di Destinazione",
      italian: "Italiano",
      french: "Francese",
      wolof: "Wolof",
      
      // Document Upload
      uploadDocument: "Carica Documento",
      uploadHint: "Supporta JPEG, PNG, GIF, PDF (max 5MB)",
      uploadPlaceholder: "Carica un'immagine o PDF",
      selectedFile: "Selezionato:",
      fileSize: "Dimensione:",
      
      // Actions
      analyzeDocument: "Analizza Documento",
      analyzingDocument: "Analizzando Documento...",
      startNewTranslation: "Inizia Nuova Traduzione",
      
      // Results
      translationComplete: "Traduzione Completata!",
      originalText: "Testo Originale",
      translatedText: "Testo Tradotto",
      documentExplanation: "Spiegazione del Documento",
      documentAnalysis: "Analisi del Documento",
      translatedTo: "Tradotto in",
      
      // Metadata
      fileName: "File:",
      detectedLanguage: "Lingua Rilevata:",
      targetLanguage: "Lingua di Destinazione:",
      processedAt: "Elaborato:",
      
      // Errors
      selectLanguageFirst: "Seleziona prima una lingua di destinazione",
      uploadDocumentFirst: "Carica prima un documento",
      invalidFileType: "Seleziona un file immagine (JPEG, PNG, GIF) o PDF",
      fileTooLarge: "La dimensione del file deve essere inferiore a 5MB",
      analysisError: "Si è verificato un errore durante l'analisi",
      
      // UI Language Selector
      uiLanguage: "Lingua Interfaccia",
      
      // View Options
      viewOptions: "Opzioni di Visualizzazione",
      sideBySide: "Affiancato",
      tabs: "Schede",
      sections: "Sezioni",
      
      // PDF Download
      downloadPDF: "Scarica PDF Tradotto",
      
      // Section Headers
      page: "Pagina",
      introduction: "Introduzione",
      instructions: "Istruzioni", 
      questions: "Domande",
      conclusion: "Conclusione",
      details: "Dettagli",
      summary: "Riassunto"
    }
  },
  fr: {
    translation: {
      // App Title and Header
      appTitle: "TAHAWU AI",
      appSubtitle: "Traduction de Documents Simplifiée",
      
      // Language Selection
      selectLanguage: "Sélectionner la Langue Cible",
      italian: "Italien",
      french: "Français",
      wolof: "Wolof",
      
      // Document Upload
      uploadDocument: "Télécharger Document",
      uploadHint: "Supporte JPEG, PNG, GIF, PDF (max 5MB)",
      uploadPlaceholder: "Télécharger une image ou PDF",
      selectedFile: "Sélectionné:",
      fileSize: "Taille:",
      
      // Actions
      analyzeDocument: "Analyser Document",
      analyzingDocument: "Analyse du Document...",
      startNewTranslation: "Commencer Nouvelle Traduction",
      
      // Results
      translationComplete: "Traduction Terminée!",
      originalText: "Texte Original",
      translatedText: "Texte Traduit",
      documentExplanation: "Explication du Document",
      documentAnalysis: "Analyse du Document",
      translatedTo: "Traduit en",
      
      // Metadata
      fileName: "Fichier:",
      detectedLanguage: "Langue Détectée:",
      targetLanguage: "Langue Cible:",
      processedAt: "Traité:",
      
      // Errors
      selectLanguageFirst: "Sélectionnez d'abord une langue cible",
      uploadDocumentFirst: "Téléchargez d'abord un document",
      invalidFileType: "Sélectionnez un fichier image (JPEG, PNG, GIF) ou PDF",
      fileTooLarge: "La taille du fichier doit être inférieure à 5MB",
      analysisError: "Une erreur s'est produite lors de l'analyse",
      
      // UI Language Selector
      uiLanguage: "Langue Interface",
      
      // View Options
      viewOptions: "Options d'Affichage",
      sideBySide: "Côte à Côte",
      tabs: "Onglets",
      sections: "Sections",
      
      // PDF Download
      downloadPDF: "Télécharger PDF Traduit",
      
      // Section Headers
      page: "Page",
      introduction: "Introduction",
      instructions: "Instructions",
      questions: "Questions", 
      conclusion: "Conclusion",
      details: "Détails",
      summary: "Résumé"
    }
  },
  wo: {
    translation: {
      // App Title and Header
      appTitle: "TAHAWU AI",
      appSubtitle: "Tektal Dokimaa ak Yaakar",
      
      // Language Selection
      selectLanguage: "Taan Làkk wi nga Bëgg",
      italian: "Talyan",
      french: "Faraañse",
      wolof: "Wolof",
      
      // Document Upload
      uploadDocument: "Yeb Dokimaa",
      uploadHint: "Mën na def ak JPEG, PNG, GIF, PDF (max 5MB)",
      uploadPlaceholder: "Yeb benn nataal walla PDF",
      selectedFile: "Taan:",
      fileSize: "Dayoo:",
      
      // Actions
      analyzeDocument: "Xoolal Dokimaa",
      analyzingDocument: "Xoolal Dokimaa...",
      startNewTranslation: "Jëkk Tektal bu Bees",
      
      // Results
      translationComplete: "Tektal Nekk!",
      originalText: "Mbind bu Njëkk",
      translatedText: "Mbind bu Tektal",
      documentExplanation: "Jagleel Dokimaa",
      documentAnalysis: "Xoolal Dokimaa",
      translatedTo: "Tektal ci",
      
      // Metadata
      fileName: "Bii:",
      detectedLanguage: "Làkk bu Gis:",
      targetLanguage: "Làkk bu Bëgg:",
      processedAt: "Defal:",
      
      // Errors
      selectLanguageFirst: "Taan bala làkk bu bëgg",
      uploadDocumentFirst: "Yeb bala dokimaa",
      invalidFileType: "Taan benn nataal (JPEG, PNG, GIF) walla PDF",
      fileTooLarge: "Dayoo bii foofu 5MB",
      analysisError: "Am na jafe ci xoolal bi",
      
      // UI Language Selector
      uiLanguage: "Làkk Interface",
      
      // View Options
      viewOptions: "Fajka Xool",
      sideBySide: "Sàmm-Sàmm",
      tabs: "Bët",
      sections: "Yëf",
      
      // Section Headers
      page: "Xët",
      introduction: "Tàmbaali",
      instructions: "Njàng",
      questions: "Laaj",
      conclusion: "Noppi",
      details: "Cistaaraan",
      summary: "Jëmmatu"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'it', // default language
    fallbackLng: 'it',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;