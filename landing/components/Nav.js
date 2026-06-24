'use client';

import { useLocale, t } from '@/lib/i18n';
import LocaleToggle from '@/components/LocaleToggle';

export default function Nav({ current = '' }) {
  const { locale, ready } = useLocale();

  const linkClass = (page) =>
    `text-sm transition-colors ${
      current === page
        ? 'text-[var(--navy)] font-medium'
        : 'text-[var(--text-secondary)] hover:text-[var(--navy)]'
    }`;

  if (!ready) return <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto w-full"><div className="text-xl font-bold text-[var(--navy)] tracking-tight">⌛</div></nav>;

  return (
    <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto w-full">
      <a href="/" className="text-xl font-bold text-[var(--navy)] tracking-tight">
        {t('nav.title', locale)}
      </a>
      <div className="flex items-center gap-5 text-sm">
        <a href="/" className={linkClass('home')}>
          {t('nav.home', locale)}
        </a>
        <a href="/how-it-works" className={linkClass('how-it-works')}>
          {t('nav.howItWorks', locale)}
        </a>
        <a href="/workspace" className={linkClass('workspace')}>
          {t('nav.workspace', locale)}
        </a>
        <LocaleToggle />
      </div>
    </nav>
  );
}
