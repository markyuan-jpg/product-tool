'use client';

import Link from 'next/link';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale, t } from '@/lib/i18n';

export default function PaymentCancelPage() {
  const { locale, ready } = useLocale();
  if (!ready) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-[var(--navy)] mb-2">{t('payment.cancelTitle', locale)}</h1>
          <p className="text-sm text-[var(--text-secondary)] mb-6">{t('payment.cancelDesc', locale)}</p>
          <div className="flex gap-3 justify-center">
            <Link href="/pricing"
              className="px-6 py-2.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-sm font-medium hover:bg-gray-50">
              {t('payment.cancelBtn', locale)}
            </Link>
            <Link href="/workspace"
              className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)]">
              {t('payment.successBtn', locale)}
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
