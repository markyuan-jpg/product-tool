'use client';

import Link from 'next/link';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function PaymentCancelPage() {
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
          <h1 className="text-xl font-bold text-[var(--navy)] mb-2">支付未完成</h1>
          <p className="text-sm text-[var(--text-secondary)] mb-6">你的支付已被取消，未产生任何扣费。如有任何问题，请联系客服。</p>
          <div className="flex gap-3 justify-center">
            <Link href="/pricing"
              className="px-6 py-2.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-sm font-medium hover:bg-gray-50">
              重新选择方案
            </Link>
            <Link href="/workspace"
              className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)]">
              返回工作台
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
