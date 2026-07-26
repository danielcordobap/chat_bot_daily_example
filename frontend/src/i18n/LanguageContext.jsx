import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import esDict from './es.json';
import enDict from './en.json';

const dictionaries = {
  es: esDict,
  en: enDict
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    const saved = localStorage.getItem('app_lang');
    if (saved === 'es' || saved === 'en') {
      return saved;
    }
    if (typeof navigator !== 'undefined' && navigator.language && navigator.language.toLowerCase().startsWith('en')) {
      return 'en';
    }
    return 'es';
  });

  const setLang = useCallback((newLang) => {
    if (newLang === 'es' || newLang === 'en') {
      setLangState(newLang);
      localStorage.setItem('app_lang', newLang);
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const t = useCallback((key, params = {}) => {
    const dict = dictionaries[lang] || dictionaries.es;
    const keys = key.split('.');
    let result = dict;

    for (const k of keys) {
      if (result && typeof result === 'object' && k in result) {
        result = result[k];
      } else {
        result = undefined;
        break;
      }
    }

    if (typeof result !== 'string') {
      console.warn(`Missing translation key: "${key}" for language "${lang}"`);
      return key;
    }

    let interpolated = result;
    if (params && typeof params === 'object') {
      Object.keys(params).forEach((pKey) => {
        interpolated = interpolated.replace(new RegExp(`\\{${pKey}\\}`, 'g'), String(params[pKey]));
      });
    }

    return interpolated;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
