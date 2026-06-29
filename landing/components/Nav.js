'use client';

import { useState, useEffect } from 'react';
import { useLocale, t } from '@/lib/i18n';
import { isLoggedIn, clearAuth } from '@/lib/auth';
import LocaleToggle from '@/components/LocaleToggle';

export default function Nav({ current = '' }) {
  const { locale, ready } = useLocale();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    const onFocus = () => setLoggedIn(isLoggedIn());
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  const handleLogout = () => {
    clearAuth();
    setLoggedIn(false);
    window.location.href = '/';
  };

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
        {loggedIn ? (
          <>
            <a href="/account" className={linkClass('account')}>
              {t('nav.account', locale)}
            </a>
            <button onClick={handleLogout} className="text-sm text-[var(--text-secondary)] hover:text-[var(--error)] transition-colors cursor-pointer">
              {t('nav.logout', locale)}
            </button>
          </>
        ) : (
          <>
            <a href="/login" className={linkClass('login')}>
              {t('nav.login', locale)}
            </a>
            <a href="/register" className="px-3 py-1 rounded-lg bg-[var(--navy)] text-white text-sm hover:bg-[var(--navy-light)] transition-colors">
              {t('nav.register', locale)}
            </a>
          </>
        )}
        <LocaleToggle />
      </div>
    </nav>
  );
}
