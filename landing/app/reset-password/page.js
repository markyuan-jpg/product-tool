'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import API_BASE from '@/lib/api';
import { friendlyError } from '@/lib/errors';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale, t } from '@/lib/i18n';

function ResetForm() {
  const { locale, ready } = useLocale();
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!ready) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!token) { setError(t('auth.errorRequired', locale)); return; }
    if (password.length < 6) { setError(t('auth.errorPassword', locale)); return; }
    if (password !== confirm) { setError(t('auth.errorRequired', locale)); return; }

    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('token', token);
      body.append('new_password', password);
      const res = await fetch(`${API_BASE}/api/auth/reset-password`, { method: 'POST', body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reset failed');
      setSuccess(true);
      setTimeout(() => router.push('/login'), 3000);
    } catch (err) {
      setError(friendlyError(err));
    }
    setLoading(false);
  };

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <p className="text-sm text-[var(--error)]">{t('auth.resetInvalid', locale)}</p>
        <a href="/forgot-password" className="text-sm text-[var(--navy)] underline underline-offset-2">{t('auth.forgotTitle', locale)}</a>
      </div>
    );
  }

  if (success) {
    return (
      <div className="text-center space-y-4">
        <p className="text-sm text-[var(--text-secondary)]">{t('auth.resetSuccess', locale)}</p>
        <a href="/login" className="text-sm text-[var(--navy)] underline underline-offset-2">{t('auth.loginNow', locale)}</a>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-xs font-medium text-[var(--text-secondary)]">{t('auth.password', locale)}</label>
        <div className="relative mt-1">
          <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder={t('auth.passwordPlaceholder', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" required />
          <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
            {showPw ? t('account.hide', locale) : t('account.show', locale)}
          </button>
        </div>
      </div>
      <div>
        <label className="text-xs font-medium text-[var(--text-secondary)]">{t('auth.confirmPassword', locale)}</label>
        <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder={t('auth.confirmPasswordPlaceholder', locale)} className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" required />
      </div>
      {error && <p className="text-xs text-[var(--error)]">{error}</p>}
      <button type="submit" disabled={loading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50">
        {loading ? t('auth.registering', locale) : t('auth.resetPassword', locale)}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  const { ready } = useLocale();
  if (!ready) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="reset-password" />
      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)]">
          <h1 className="text-2xl font-bold text-[var(--navy)] text-center mb-6">Reset Password</h1>
          <Suspense fallback={<p className="text-sm text-center">Loading...</p>}>
            <ResetForm />
          </Suspense>
        </div>
      </section>
      <Footer />
    </div>
  );
}
