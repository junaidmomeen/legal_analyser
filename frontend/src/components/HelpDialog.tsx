import React from 'react';
import { X, Keyboard, Upload, Search, FileText, Lightbulb } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';

interface HelpDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const HelpDialog: React.FC<HelpDialogProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();

  const shortcuts = [
    { keys: ['Ctrl', 'U'], description: t('help.shortcutUpload') },
    { keys: ['Ctrl', 'N'], description: t('help.shortcutNewAnalysis') },
    { keys: ['Ctrl', 'F'], description: t('help.shortcutSearch') },
    { keys: ['Escape'], description: t('help.shortcutEscape') },
    { keys: ['F1'], description: t('help.shortcutHelp') },
  ];

  const steps = [
    { icon: Upload, text: t('help.step1') },
    { icon: Search, text: t('help.step2') },
    { icon: FileText, text: t('help.step3') },
    { icon: Lightbulb, text: t('help.step4') },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Dialog */}
          <motion.div
            className="fixed inset-4 md:inset-8 lg:inset-16 bg-base-200 border border-base-300 rounded-xl shadow-2xl z-50 flex flex-col max-w-4xl mx-auto"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
            aria-describedby="help-description"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-base-300">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-primary-600 rounded-lg">
                  <Lightbulb className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 id="help-title" className="text-xl font-bold text-neutral-200">
                    {t('help.title')}
                  </h2>
                  <p id="help-description" className="text-sm text-neutral-400">
                    Learn how to use the Legal Document Analyzer
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-base-300 rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-base-200"
                aria-label={t('accessibility.closeDialog')}
              >
                <X className="h-5 w-5 text-neutral-400" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              {/* Getting Started */}
              <section>
                <h3 className="text-lg font-semibold text-neutral-200 mb-4">
                  {t('help.gettingStarted')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {steps.map((step, index) => (
                    <motion.div
                      key={index}
                      className="flex items-start space-x-3 p-4 bg-base-100 rounded-lg border border-base-300"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <div className="p-2 bg-primary-600 rounded-lg flex-shrink-0">
                        <step.icon className="h-4 w-4 text-white" />
                      </div>
                      <p className="text-sm text-neutral-300">{step.text}</p>
                    </motion.div>
                  ))}
                </div>
              </section>

              {/* Supported Formats */}
              <section>
                <h3 className="text-lg font-semibold text-neutral-200 mb-4">
                  {t('help.supportedFormats')}
                </h3>
                <div className="p-4 bg-base-100 rounded-lg border border-base-300">
                  <p className="text-sm text-neutral-300">
                    {t('help.supportedFormatsDesc')}
                  </p>
                </div>
              </section>

              {/* Keyboard Shortcuts */}
              <section>
                <h3 className="text-lg font-semibold text-neutral-200 mb-4 flex items-center space-x-2">
                  <Keyboard className="h-5 w-5" />
                  <span>{t('help.keyboardShortcuts')}</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {shortcuts.map((shortcut, index) => (
                    <motion.div
                      key={index}
                      className="flex items-center justify-between p-3 bg-base-100 rounded-lg border border-base-300"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <span className="text-sm text-neutral-300">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center space-x-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <React.Fragment key={keyIndex}>
                            <kbd className="px-2 py-1 text-xs font-mono bg-base-300 text-neutral-200 rounded border border-base-400">
                              {key}
                            </kbd>
                            {keyIndex < shortcut.keys.length - 1 && (
                              <span className="text-neutral-400 text-xs">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </section>
            </div>

            {/* Footer */}
            <div className="flex justify-end p-6 border-t border-base-300">
              <button
                onClick={onClose}
                className="btn-primary"
              >
                {t('actions.close')}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default HelpDialog;
