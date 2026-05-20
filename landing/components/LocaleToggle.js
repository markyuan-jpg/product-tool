'use client';

import { useLocale } from '@/lib/i18n';

export default function LocaleToggle() {
  const { locale, switchLocale } = useLocale();

  return (
    <button
      onClick={() => switchLocale(locale === 'zh' ? 'en' : 'zh')}
      className="text-xs px-2 py-1 rounded border border-[var(--border)] text-[var(--text-secondary)] hover:bg-gray-50 transition-colors cursor-pointer"
      title={locale === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      {locale === 'zh' ? 'EN' : '中文'}
    </button>
  );
}
