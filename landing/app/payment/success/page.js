'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { verifyAuth } from '@/lib/auth';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const [status, setStatus] = useState('verifying');

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
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">正在确认支付...</h1>
              <p className="text-sm text-[var(--text-secondary)]">请稍候，正在激活你的专业版权限</p>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-[var(--success)] rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">支付成功！</h1>
              <p className="text-sm text-[var(--text-secondary)] mb-6">你已成功升级为专业版用户，现在可以使用全部功能。</p>
              <button onClick={() => router.push('/workspace')}
                className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] cursor-pointer">
                前往工作台
              </button>
            </>
          )}
          {status === 'pending' && (
            <>
              <h1 className="text-xl font-bold text-[var(--navy)] mb-2">支付已收到</h1>
              <p className="text-sm text-[var(--text-secondary)] mb-4">专业版权限正在激活中，通常需要 1-2 分钟。</p>
              <p className="text-sm text-[var(--text-secondary)] mb-6">如果长时间未激活，请联系客服。</p>
              <button onClick={() => router.push('/workspace')}
                className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] cursor-pointer">
                返回工作台
              </button>
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
