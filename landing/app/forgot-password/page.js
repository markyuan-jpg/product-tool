'use client';

import { useState } from 'react';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function ForgotPasswordPage() {
  const [showContact, setShowContact] = useState(false);
  const wechatId = 'yb857151464';

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="forgot-password" />

      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)] text-center">
          <h1 className="text-2xl font-bold text-[var(--navy)] mb-4">忘记密码</h1>
          <p className="text-sm text-[var(--text-secondary)] mb-6">请联系客服重置密码</p>

          {showContact && (
            <div className="mb-6 p-4 border border-[var(--border)] rounded-lg bg-[var(--warm-white)]">
              <p className="text-sm text-[var(--text-primary)] mb-2">
                微信：<span className="font-mono font-medium text-[var(--navy)]">{wechatId}</span>
              </p>
              <p className="text-xs text-[var(--text-secondary)]">添加微信时请备注"密码重置"</p>
            </div>
          )}

          <button
            onClick={() => setShowContact(!showContact)}
            className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors cursor-pointer"
          >
            {showContact ? '收起联系方式' : '联系客服'}
          </button>

          <p className="text-xs text-[var(--text-secondary)] mt-4">
            <a href="/login" className="text-[var(--navy)] underline underline-offset-2">返回登录</a>
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
