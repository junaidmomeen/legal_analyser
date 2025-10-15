import React from 'react';
import { Globe, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

const languages: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
];

const LanguageSelector: React.FC = () => {
  const { i18n, t } = useTranslation();

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
  };

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  return (
    <div className="relative group">
      <button
        className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-base-200 hover:bg-base-300 transition-colors duration-200 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-base-100"
        aria-label={t('accessibility.selectLanguage')}
        aria-expanded="false"
        aria-haspopup="true"
        id="language-selector"
      >
        <Globe className="h-4 w-4 text-neutral-400" />
        <span className="text-sm font-medium text-neutral-200">
          {currentLanguage.flag} {currentLanguage.code.toUpperCase()}
        </span>
      </button>

      <div className="absolute right-0 mt-2 w-48 bg-base-200 border border-base-300 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
        <div className="py-1" role="menu" aria-labelledby="language-selector">
          {languages.map((language) => (
            <button
              key={language.code}
              className={`w-full flex items-center justify-between px-4 py-2 text-sm hover:bg-base-300 transition-colors duration-200 focus:bg-base-300 focus:outline-none ${
                language.code === i18n.language ? 'text-primary-400' : 'text-neutral-200'
              }`}
              onClick={() => handleLanguageChange(language.code)}
              role="menuitem"
              aria-current={language.code === i18n.language ? 'true' : 'false'}
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">{language.flag}</span>
                <div className="text-left">
                  <div className="font-medium">{language.nativeName}</div>
                  <div className="text-xs text-neutral-400">{language.name}</div>
                </div>
              </div>
              {language.code === i18n.language && (
                <Check className="h-4 w-4 text-primary-400" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LanguageSelector;
