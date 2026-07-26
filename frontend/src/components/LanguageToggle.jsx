import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

export default function LanguageToggle() {
  const { lang, setLang, t } = useLanguage();

  return (
    <div className="language-toggle-container" role="group" aria-label={t('language.label')}>
      <button
        type="button"
        className={`lang-btn ${lang === 'es' ? 'active' : ''}`}
        aria-pressed={lang === 'es'}
        title={t('language.switchTo', { lang: t('language.es') })}
        onClick={() => setLang('es')}
      >
        ES
      </button>
      <button
        type="button"
        className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
        aria-pressed={lang === 'en'}
        title={t('language.switchTo', { lang: t('language.en') })}
        onClick={() => setLang('en')}
      >
        EN
      </button>
    </div>
  );
}
