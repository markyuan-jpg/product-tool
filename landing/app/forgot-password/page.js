'use client';

import { useState } from 'react';
import { useLocale, t } from '@/lib/i18n';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function ForgotPasswordPage() {
  const { locale, ready } = useLocale();
  const [showContact, setShowContact] = useState(false);
  const wechatId = 'yb857151464';

  if (!ready) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="forgot-password" />

      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)] text-center">
          <h1 className="text-2xl font-bold text-[var(--navy)] mb-4">{t('auth.forgotTitle', locale)}</h1>
          <p className="text-sm text-[var(--text-secondary)] mb-6">{t('auth.forgotDesc', locale)}</p>

          {showContact && (
            <div className="mb-6 p-4 border border-[var(--border)] rounded-lg bg-[var(--warm-white)]">
              <p className="text-sm text-[var(--text-primary)] mb-2">
                 {t('auth.forgotWechat', locale)}<span className="font-mono font-medium text-[var(--navy)]">{wechatId}</span>
              </p>
              <p className="text-xs text-[var(--text-secondary)]">{t('auth.forgotWechatNote', locale)}</p>
            </div>
          )}

          <button
            onClick={() => setShowContact(!showContact)}
            className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors cursor-pointer"
          >
            {showContact ? t('auth.forgotCollapse', locale) : t('auth.contactAdmin', locale)}
          </button>

          <p className="text-xs text-[var(--text-secondary)] mt-4">
            <a href="/login" className="text-[var(--navy)] underline underline-offset-2">{t('auth.backToLogin', locale)}</a>
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
