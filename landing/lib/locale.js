'use client';

const STORAGE_KEY = 'app_locale';

export function getStoredLocale() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setStoredLocale(locale) {
  localStorage.setItem(STORAGE_KEY, locale);
}

export async function detectLocale() {
  const stored = getStoredLocale();
  if (stored) return stored;

  try {
    const controller = new AbortController();
    const tid = setTimeout(() => controller.abort(), 2000);
    const res = await fetch('https://ip-api.com/json/?fields=countryCode', { signal: controller.signal });
    clearTimeout(tid);
    const data = await res.json();
    return data.countryCode === 'CN' ? 'zh' : 'en';
  } catch {
    return 'zh';
  }
}
