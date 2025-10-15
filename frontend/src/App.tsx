import { useState, useEffect } from 'react';
import { FileText, HelpCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet-async';
import { motion, AnimatePresence } from 'framer-motion';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import AnalysisReportSkeleton from './components/AnalysisReportSkeleton';
import ConfirmationDialog from './components/ConfirmationDialog';
import LanguageSelector from './components/LanguageSelector';
import HelpDialog from './components/HelpDialog';
import { analyzeDocument, exportAnalysis, viewOriginalDocument, getSupportedFormats, AnalysisResult, SupportedFormats, ApiError, clearHistory } from './api/api';
import { useKeyboardShortcuts, useFocusManagement } from './hooks/useAccessibility';

const Header: React.FC<{ onHelpClick: () => void }> = ({ onHelpClick }) => {
  const { t } = useTranslation();

  return (
    <header className="glass sticky top-0 z-10 border-b border-base-300">
      <div className="container-safe py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-primary-600 rounded-lg shadow-md">
              <FileText className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-neutral-200 tracking-tight">
                {t('app.title')}
              </h1>
              <p className="text-neutral-400 text-sm">{t('app.subtitle')}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={onHelpClick}
              className="p-2 hover:bg-base-300 rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-base-100"
              aria-label={t('accessibility.showHelp')}
            >
              <HelpCircle className="h-5 w-5 text-neutral-400" />
            </button>
            <LanguageSelector />
          </div>
        </div>
      </div>
    </header>
  );
};

function App() {
  const { t } = useTranslation();
  const { handleShortcut } = useKeyboardShortcuts();
  const { focusUploadArea, focusSearch, focusNewAnalysis } = useFocusManagement();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [supportedFormats, setSupportedFormats] = useState<SupportedFormats | null>(null);
  const [originalFileId, setOriginalFileId] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showHelp, setShowHelp] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const cleanupUpload = handleShortcut(focusUploadArea, ['ctrl+u']);
    const cleanupNewAnalysis = handleShortcut(() => {
      if (analysis) {
        focusNewAnalysis();
      }
    }, ['ctrl+n']);
    const cleanupSearch = handleShortcut(focusSearch, ['ctrl+f']);
    const cleanupHelp = handleShortcut(() => setShowHelp(true), ['f1']);
    const cleanupEscape = handleShortcut(() => {
      if (showHelp) setShowHelp(false);
      if (showConfirmation) setShowConfirmation(false);
    }, ['escape']);

    return () => {
      cleanupUpload();
      cleanupNewAnalysis();
      cleanupSearch();
      cleanupHelp();
      cleanupEscape();
    };
  }, [handleShortcut, focusUploadArea, focusNewAnalysis, focusSearch, analysis, showHelp, showConfirmation]);

  useEffect(() => {
    const fetchSupportedFormats = async () => {
      try {
        const formats = await getSupportedFormats();
        setSupportedFormats(formats);
      } catch (error) {
        console.error("Failed to fetch supported formats:", error);
        setError({ message: t('errors.backendConnection') });
      }
    };
    fetchSupportedFormats();
  }, [t]);

  const handleFileSelect = (file: File | null) => {
    setError(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!supportedFormats) {
      setError({ message: t('errors.formatsNotLoaded') });
      return;
    }

    const allowedExtensions = supportedFormats.formats.map(f => `.${f.toLowerCase()}`);
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    const isValidExtension = allowedExtensions.includes(fileExtension);

    if (isValidExtension) {
      setSelectedFile(file);
    } else {
      setError({ 
        message: t('errors.unsupportedFileType', { types: allowedExtensions.join(', ') }) 
      });
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setIsAnalyzing(true);
    setError(null);
    setUploadProgress(0);
    try {
      const result = await analyzeDocument(selectedFile, setUploadProgress);
      setAnalysis(result);
      setOriginalFileId(result.file_id??null);
    } catch (err: unknown) {
      console.error("Analysis error:", err);
      setError({ message: t('errors.analysisFailed') });
    } finally {
      setIsAnalyzing(false);
      setUploadProgress(0);
    }
  };

  const handleExport = async (format: 'pdf' | 'json') => {
    if (!originalFileId) return;
    
    // Clear any existing errors
    setError(null);
    
    try {
      await exportAnalysis(originalFileId, format);
      // Success - file should download automatically
    } catch (err: unknown) {
      console.error(`Export error for ${format}:`, err);
      setError({ 
        message: err instanceof Error ? err.message : t('errors.exportFailed', { format: format.toUpperCase() }) 
      });
    }
  };

  const handleViewOriginal = async () => {
    if (!originalFileId) return;
    try {
      await viewOriginalDocument(originalFileId);
    } catch (err: unknown) {
      console.error("View original error:", err);
      setError({ message: t('errors.viewOriginalFailed') });
    }
  };

  const handleClearHistory = () => {
    if (analysis) {
      setShowConfirmation(true);
    } else {
      reset();
    }
  };

  const reset = async () => {
    try {
      await clearHistory();
    } catch (error) {
      console.error("Failed to clear history:", error);
      setError({ message: t('errors.clearHistoryFailed') });
    }
    setSelectedFile(null);
    setAnalysis(null);
    setError(null);
    setOriginalFileId(null);
    setShowConfirmation(false);
  };

  return (
    <>
      <Helmet>
        <title>{t('app.title')}</title>
        <meta name="description" content={t('app.subtitle')} />
        <html lang={t('i18n.language')} />
      </Helmet>
      
      <div className="min-h-screen bg-base-100 text-neutral-200 font-sans">
        {/* Skip link for accessibility */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        
        <Header onHelpClick={() => setShowHelp(true)} />
        
        <main id="main-content" className="container-safe py-8">
          <AnimatePresence mode="wait">
            {isAnalyzing ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <AnalysisReportSkeleton />
              </motion.div>
            ) : analysis ? (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Dashboard
                  analysis={analysis}
                  onExport={handleExport}
                  onViewOriginal={handleViewOriginal}
                  onClearHistory={handleClearHistory}
                  onReset={reset}
                  selectedFile={selectedFile}
                />
              </motion.div>
            ) : (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <FileUpload 
                  onFileSelect={handleFileSelect}
                  onAnalyze={handleAnalyze}
                  isAnalyzing={isAnalyzing}
                  selectedFile={selectedFile}
                  supportedFormats={supportedFormats}
                  error={error}
                  onErrorClose={() => setError(null)}
                  uploadProgress={uploadProgress}
                />
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence>
            {showConfirmation && (
              <ConfirmationDialog 
                message={t('confirmation.clearHistory')}
                onConfirm={reset}
                onCancel={() => setShowConfirmation(false)}
              />
            )}
          </AnimatePresence>
        </main>
        
        <HelpDialog 
          isOpen={showHelp}
          onClose={() => setShowHelp(false)}
        />
      </div>
    </>
  );
}

export default App;