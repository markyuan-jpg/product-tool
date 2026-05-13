'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import API_BASE from '@/lib/api';
import { saveToken } from '@/lib/auth';
import { friendlyError } from '@/lib/errors';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setError('用户名仅限英文、数字、下划线');
      return;
    }
    if (password.length < 6) {
      setError('密码至少 6 位');
      return;
    }
    if (password !== confirm) {
      setError('两次密码不一致');
      return;
    }

    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const res = await fetch(`${API_BASE}/api/auth/register`, { method: 'POST', body, signal: controller.signal });
      clearTimeout(timeoutId);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '注册失败');
      saveToken(data.token, data.user);
      router.push('/workspace');
    } catch (err) {
      setError(friendlyError(err));
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="register" />

      <section className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm border border-[var(--border)] rounded-xl p-8 bg-[var(--surface)]">
          <h1 className="text-2xl font-bold text-[var(--navy)] text-center mb-6">注册</h1>
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-[var(--text-secondary)]">用户名</label>
              <input value={username} onChange={e => setUsername(e.target.value)} placeholder="英文、数字、下划线" className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" required />
            </div>
            <div>
              <label className="text-xs font-medium text-[var(--text-secondary)]">密码</label>
              <div className="relative mt-1">
                <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="至少 6 位" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" required />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                  {showPw ? '隐藏' : '显示'}
                </button>
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-[var(--text-secondary)]">确认密码</label>
              <div className="relative mt-1">
                <input type={showConfirm ? 'text' : 'password'} value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="再次输入密码" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" required />
                <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                  {showConfirm ? '隐藏' : '显示'}
                </button>
              </div>
            </div>
            {error && <p className="text-xs text-[var(--error)]">{error}</p>}
            <button type="submit" disabled={loading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50">
              {loading ? '注册中...' : '注册'}
            </button>
          </form>
          <p className="text-xs text-[var(--text-secondary)] text-center mt-4">
            已有账号？<a href="/login" className="text-[var(--navy)] underline underline-offset-2">登录</a>
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
