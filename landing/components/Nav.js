'use client';

import { useState, useEffect } from 'react';
import { isLoggedIn, getStoredUser, clearAuth } from '@/lib/auth';
import { useLocale, t } from '@/lib/i18n';
import LocaleToggle from '@/components/LocaleToggle';

export default function Nav({ current = '' }) {
  const [authUser, setAuthUser] = useState(null);
  const { locale, ready } = useLocale();

  useEffect(() => {
    if (isLoggedIn()) setAuthUser(getStoredUser());
  }, []);

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
        <a href="/pricing" className={linkClass('pricing')}>
          {t('nav.pricing', locale)}
        </a>
        {authUser ? (
          <>
            <a href="/workspace" className={linkClass('workspace')}>
              {t('nav.workspace', locale)}
            </a>
            <a
              href="/account"
              className="text-[var(--navy)] font-medium text-sm"
            >
              {authUser.username}
            </a>
            <button
              onClick={() => { clearAuth(); setAuthUser(null); }}
              className="text-[var(--text-secondary)] hover:text-[var(--error)] transition-colors cursor-pointer text-sm"
            >
              {t('nav.logout', locale)}
            </button>
          </>
        ) : (
          <a
            href="/login"
            className="px-3 py-1.5 rounded-lg bg-[var(--navy)] text-white text-xs font-medium hover:bg-[var(--navy-light)] transition-colors"
          >
            {t('nav.login', locale)}
          </a>
        )}
        <LocaleToggle />
      </div>
    </nav>
  );
}
