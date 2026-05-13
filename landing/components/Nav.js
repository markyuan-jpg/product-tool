'use client';

import { useState, useEffect } from 'react';
import { isLoggedIn, getStoredUser, clearAuth } from '@/lib/auth';

export default function Nav({ current = '' }) {
  const [authUser, setAuthUser] = useState(null);

  useEffect(() => {
    if (isLoggedIn()) setAuthUser(getStoredUser());
  }, []);

  const linkClass = (page) =>
    `text-sm transition-colors ${
      current === page
        ? 'text-[var(--navy)] font-medium'
        : 'text-[var(--text-secondary)] hover:text-[var(--navy)]'
    }`;

  return (
    <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto w-full">
      <a href="/" className="text-xl font-bold text-[var(--navy)] tracking-tight">
        报价整合工具
      </a>
      <div className="flex items-center gap-5 text-sm">
        <a href="/" className={linkClass('home')}>
          主页
        </a>
        <a href="/how-it-works" className={linkClass('how-it-works')}>
          工作原理
        </a>
        <a href="/pricing" className={linkClass('pricing')}>
          定价
        </a>
        {authUser ? (
          <>
            <a href="/workspace" className={linkClass('workspace')}>
              工作台
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
              退出
            </button>
          </>
        ) : (
          <a
            href="/login"
            className="px-3 py-1.5 rounded-lg bg-[var(--navy)] text-white text-xs font-medium hover:bg-[var(--navy-light)] transition-colors"
          >
            登录
          </a>
        )}
      </div>
    </nav>
  );
}
