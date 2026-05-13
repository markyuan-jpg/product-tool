'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import API_BASE from '@/lib/api';
import { saveToken } from '@/lib/auth';
import { friendlyError } from '@/lib/errors';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const res = await fetch(`${API_BASE}/api/auth/login`, { method: 'POST', body, signal: controller.signal });
      clearTimeout(timeoutId);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '登录失败');
      saveToken(data.token, data.user);
      router.push('/workspace');
    } catch (err) {
      setError(friendlyError(err));
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="login" />

      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)]">
          <h1 className="text-2xl font-bold text-[var(--navy)] text-center mb-6">登录</h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-[var(--text-secondary)]">用户名</label>
              <input value={username} onChange={e => setUsername(e.target.value)} placeholder="输入用户名" className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" required />
            </div>
            <div>
              <label className="text-xs font-medium text-[var(--text-secondary)]">密码</label>
              <div className="relative mt-1">
                <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="输入密码" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" required />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                  {showPw ? '隐藏' : '显示'}
                </button>
              </div>
            </div>
            {error && <p className="text-xs text-[var(--error)]">{error}</p>}
            <button type="submit" disabled={loading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50">
              {loading ? '登录中...' : '登录'}
            </button>
            <div className="flex justify-between text-xs">
              <a href="/forgot-password" className="text-[var(--text-secondary)] hover:text-[var(--navy)] underline underline-offset-2">忘记密码？</a>
            </div>
          </form>
          <p className="text-xs text-[var(--text-secondary)] text-center mt-4">
            没有账号？<a href="/register" className="text-[var(--navy)] underline underline-offset-2">注册</a>
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
