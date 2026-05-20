'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { detectLocale, setStoredLocale, getStoredLocale } from './locale';

import zh from '@/translations/zh.json';
import en from '@/translations/en.json';

const LOCALES = { zh, en };
export const LocaleContext = createContext();

export function LocaleProvider({ children }) {
  const [locale, setLocale] = useState('zh');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = getStoredLocale();
    if (stored) {
      setLocale(stored);
      setReady(true);
    } else {
      detectLocale()
        .then((detected) => {
          setLocale(detected);
          setStoredLocale(detected);
        })
        .catch(() => {})
        .finally(() => setReady(true));
    }
  }, []);

  const switchLocale = useCallback((newLocale) => {
    setLocale(newLocale);
    setStoredLocale(newLocale);
    document.documentElement.lang = newLocale === 'zh' ? 'zh-CN' : 'en';
  }, []);

  return (
    <LocaleContext.Provider value={{ locale, ready, switchLocale }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider');
  return ctx;
}

/** Translate key. Supports dot notation: t('nav.home') */
export function t(key, locale) {
  const keys = key.split('.');
  let val = LOCALES[locale];
  for (const k of keys) {
    if (val && typeof val === 'object') val = val[k];
    else return key; // fallback to key
  }
  return typeof val === 'string' ? val : key;
}
