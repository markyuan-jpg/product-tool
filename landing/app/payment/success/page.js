'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { verifyAuth } from '@/lib/auth';
import { useLocale, t } from '@/lib/i18n';

export default function PaymentSuccessPage() {
  const { locale, ready } = useLocale();
  const router = useRouter();
  const [status, setStatus] = useState('verifying');

  if (!ready) return null;

  useEffect(() => {
    const check = async () => {
      // Wait a moment for webhook to process
      await new Promise(r => setTimeout(r, 2000));
      const user = await verifyAuth();
      if (user && user.tier === 'pro') {
        setStatus('success');
      } else {
        setStatus('pending');
      }
    };
    check();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          {status === 'verifying' && (
            <>
              <div className="w-12 h-12 border-3 border-[var(--gold)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">{t('payment.verifying', locale)}</h1>
              <p className="text-sm text-[var(--text-secondary)]">{t('payment.verifyingDesc', locale)}</p>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-[var(--success)] rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">{t('payment.successTitle', locale)}</h1>
              <p className="text-sm text-[var(--text-secondary)] mb-6">{t('payment.successDesc', locale)}</p>
              <button onClick={() => router.push('/workspace')}
                className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] cursor-pointer">
                {t('payment.successBtn', locale)}
              </button>
            </>
          )}
          {status === 'pending' && (
            <>
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">{t('payment.pending', locale)}</h1>
              <p className="text-sm text-[var(--text-secondary)] mb-4">{t('payment.pendingDesc', locale)}</p>
              <p className="text-sm text-[var(--text-secondary)] mb-6">{t('payment.contactSupport', locale)}</p>
              <button onClick={() => router.push('/workspace')}
                className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] cursor-pointer">
                {t('payment.successBtn', locale)}
              </button>
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
