'use client';

import { useState } from 'react';
import API_BASE from '@/lib/api';
import { friendlyError } from '@/lib/errors';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale, t } from '@/lib/i18n';

export default function ForgotPasswordPage() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setError(t('auth.errorEmail', locale));
      return;
    }
    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('email', email);
      const res = await fetch(`${API_BASE}/api/auth/forgot-password`, { method: 'POST', body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t('auth.registerFailed', locale));
      setSent(true);
    } catch (err) {
      setError(friendlyError(err));
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="forgot-password" />

      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)]">
          <h1 className="text-2xl font-bold text-[var(--navy)] text-center mb-6">{t('auth.forgotTitle', locale)}</h1>

          {sent ? (
            <div className="text-center space-y-4">
              <p className="text-sm text-[var(--text-secondary)]">{t('auth.forgotSent', locale)}</p>
              <a href="/login" className="text-sm text-[var(--navy)] underline underline-offset-2">{t('auth.backToLogin', locale)}</a>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-[var(--text-secondary)]">{t('auth.email', locale)}</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={t('auth.emailPlaceholder', locale)} className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" required />
              </div>
              {error && <p className="text-xs text-[var(--error)]">{error}</p>}
              <button type="submit" disabled={loading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50">
                {loading ? t('auth.registering', locale) : t('auth.forgotSubmit', locale)}
              </button>
            </form>
          )}

          <p className="text-xs text-[var(--text-secondary)] text-center mt-4">
            <a href="/login" className="text-[var(--navy)] underline underline-offset-2">{t('auth.backToLogin', locale)}</a>
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
