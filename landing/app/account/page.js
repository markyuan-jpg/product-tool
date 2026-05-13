'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isLoggedIn, getStoredUser, clearAuth } from '@/lib/auth';
import API_BASE from '@/lib/api';

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [usage, setUsage] = useState(null);
  const [showPwChange, setShowPwChange] = useState(false);
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [showOldPw, setShowOldPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [pwMsg, setPwMsg] = useState('');
  const [pwMsgType, setPwMsgType] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [showCompany, setShowCompany] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [companyNameEn, setCompanyNameEn] = useState('');
  const [companyAddress, setCompanyAddress] = useState('');
  const [companyAddressEn, setCompanyAddressEn] = useState('');
  const [companyCity, setCompanyCity] = useState('');
  const [companyContact, setCompanyContact] = useState('');
  const [companyPhone, setCompanyPhone] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [companyWebsite, setCompanyWebsite] = useState('');
  const [companyLogo, setCompanyLogo] = useState(null);
  const [companyLogoPreview, setCompanyLogoPreview] = useState('');
  const [companyMsg, setCompanyMsg] = useState('');
  const [bankBeneficiary, setBankBeneficiary] = useState('');
  const [bankName, setBankName] = useState('');
  const [bankAddress, setBankAddress] = useState('');
  const [bankAccount, setBankAccount] = useState('');
  const [bankSwift, setBankSwift] = useState('');
  const [bankMsg, setBankMsg] = useState('');

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    setUser(getStoredUser());
    fetch(`${API_BASE}/api/user/usage`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    }).then(r => r.json()).then(setUsage).catch(e => console.error('Failed to load usage:', e));
    // 加载公司信息
    fetch(`${API_BASE}/api/template?user_id=${getStoredUser()?.id || 'local'}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    }).then(r => r.json()).then(d => {
      if (d.name) setCompanyName(d.name);
      if (d.name_en) setCompanyNameEn(d.name_en);
      if (d.address) setCompanyAddress(d.address);
      if (d.address_en) setCompanyAddressEn(d.address_en);
      if (d.city) setCompanyCity(d.city);
      if (d.contact_person) setCompanyContact(d.contact_person);
      if (d.tel) setCompanyPhone(d.tel);
      if (d.email) setCompanyEmail(d.email);
      if (d.website) setCompanyWebsite(d.website);
      if (d.logo_path) setCompanyLogoPreview(`${API_BASE}/api/images?path=${encodeURIComponent(d.logo_path)}`);
    }).catch(e => console.error('Failed to load company info:', e));
    // 检查各文档模板状态
    ['quotation','pi','packing','invoice'].forEach(async (type) => {
      try {
        const r = await fetch(`${API_BASE}/api/template/document/${type}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        const d = await r.json();
        const el = document.getElementById(`tmpl-status-${type}`);
        if (el) el.textContent = d.exists ? `✅ 已上传 (${(d.size/1024).toFixed(0)}KB)` : '未上传';
      } catch(e) {}
    });
    // 从 localStorage 加载银行信息（隐私数据，不上传服务器）
    try {
      const stored = JSON.parse(localStorage.getItem('bank_info') || '{}');
      if (stored.beneficiary) setBankBeneficiary(stored.beneficiary);
      if (stored.bank_name) setBankName(stored.bank_name);
      if (stored.bank_address) setBankAddress(stored.bank_address);
      if (stored.account_no) setBankAccount(stored.account_no);
      if (stored.swift_code) setBankSwift(stored.swift_code);
    } catch (e) {}
  }, [router]);

  const handleLogout = () => { clearAuth(); router.push('/'); };

  const handleChangePw = async (e) => {
    e.preventDefault();
    setPwMsg('');
    if (!oldPw || !newPw) { setPwMsg('请填写所有字段'); setPwMsgType('error'); return; }
    if (newPw.length < 6) { setPwMsg('新密码至少6位'); setPwMsgType('error'); return; }
    setPwLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('old_password', oldPw);
      body.append('new_password', newPw);
      const res = await fetch(`${API_BASE}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '修改失败');
      setPwMsg('密码修改成功');
      setPwMsgType('success');
      setOldPw('');
      setNewPw('');
    } catch (err) {
      setPwMsg(err.message);
      setPwMsgType('error');
    }
    setPwLoading(false);
  };

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto w-full">
        <a href="/" className="text-xl font-bold text-[var(--navy)] tracking-tight">报价整合工具</a>
        <div className="flex items-center gap-5 text-sm">
          <a href="/" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">主页</a>
          <a href="/how-it-works" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">工作原理</a>
          <a href="/pricing" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">定价</a>
          <a href="/workspace" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">工作台</a>
          <div className="relative group">
            <button className="flex items-center gap-1 text-[var(--navy)] font-medium cursor-pointer">
              {user.username} <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white border border-[var(--border)] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
              <span className="block px-4 py-2 text-sm font-medium text-[var(--navy)] bg-gray-50 rounded-t-lg">账户设置</span>
              <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-[var(--error)] hover:bg-red-50 rounded-b-lg cursor-pointer">退出登录</button>
            </div>
          </div>
        </div>
      </nav>

      <section className="flex-1 max-w-md mx-auto w-full px-6 pt-16">
        <h1 className="text-2xl font-bold text-[var(--navy)] mb-6">账户管理</h1>

        <div className="border border-[var(--border)] rounded-xl p-6 bg-[var(--surface)] space-y-4">
          <div className="flex justify-between text-sm">
            <span className="text-[var(--text-secondary)]">用户名</span>
            <span className="font-medium text-[var(--navy)]">{user.username}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[var(--text-secondary)]">等级</span>
            <span className={`font-medium ${user.tier === 'pro' ? 'text-[var(--gold)]' : 'text-[var(--text-secondary)]'}`}>
              {user.tier === 'pro' ? '专业版' : '免费版'}
            </span>
          </div>
          {usage && (
            <div className="flex justify-between text-sm">
              <span className="text-[var(--text-secondary)]">本月上传</span>
              <span className="font-medium text-[var(--navy)]">{usage.upload_count} / {usage.limit} 次</span>
            </div>
          )}
        </div>

        {/* 公司信息 */}
        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <button
            onClick={() => setShowCompany(!showCompany)}
            className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-[var(--warm-white)] transition-colors cursor-pointer"
          >
            <span className="text-sm font-medium text-[var(--navy)]">公司信息</span>
            <span className="text-xs text-[var(--text-secondary)]">用于报价单 / PI / 装箱单 / 发票</span>
            <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${showCompany ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showCompany && (
            <div className="px-5 pb-5 border-t border-[var(--border)] pt-4 space-y-3">
              <input type="text" value={companyName} onChange={e => setCompanyName(e.target.value)}
                placeholder="公司中文名称" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyNameEn} onChange={e => setCompanyNameEn(e.target.value)}
                placeholder="公司英文名称" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyAddress} onChange={e => setCompanyAddress(e.target.value)}
                placeholder="公司地址（中文）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyAddressEn} onChange={e => setCompanyAddressEn(e.target.value)}
                placeholder="公司地址（英文）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyCity} onChange={e => setCompanyCity(e.target.value)}
                placeholder="所在城市（用于 FOB XX）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <div className="grid grid-cols-2 gap-3">
                <input type="text" value={companyPhone} onChange={e => setCompanyPhone(e.target.value)}
                  placeholder="电话" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
                <input type="text" value={companyEmail} onChange={e => setCompanyEmail(e.target.value)}
                  placeholder="邮箱" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              </div>
              <input type="text" value={companyWebsite} onChange={e => setCompanyWebsite(e.target.value)}
                placeholder="网站（选填）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyContact} onChange={e => setCompanyContact(e.target.value)}
                placeholder="联系人（选填）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />

              {/* 银行信息（仅本地存储） */}
              <div className="border-t border-[var(--border)] pt-3 mt-2">
                <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">银行信息（仅保存在本地浏览器，用于 PI / 商业发票）</p>
                <p className="text-[10px] text-gray-400 mb-2">不发送到服务器，生成文档时随请求传递</p>
                <input type="text" value={bankBeneficiary} onChange={e => setBankBeneficiary(e.target.value)}
                  placeholder="收款人（Beneficiary）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankName} onChange={e => setBankName(e.target.value)}
                  placeholder="银行名称（Bank Name）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankAddress} onChange={e => setBankAddress(e.target.value)}
                  placeholder="银行地址（Bank Address）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankAccount} onChange={e => setBankAccount(e.target.value)}
                  placeholder="银行账号（Account No.）" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankSwift} onChange={e => setBankSwift(e.target.value)}
                  placeholder="Swift Code" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
                {bankMsg && <p className="text-xs text-[var(--success)] mt-1">{bankMsg}</p>}
                <button onClick={() => {
                  localStorage.setItem('bank_info', JSON.stringify({
                    beneficiary: bankBeneficiary, bank_name: bankName,
                    bank_address: bankAddress, account_no: bankAccount,
                    swift_code: bankSwift,
                  }));
                  setBankMsg('银行信息已保存到本地');
                  setTimeout(() => setBankMsg(''), 3000);
                }} className="mt-2 w-full py-2 rounded-lg border border-[var(--gold)] text-[var(--navy)] text-sm font-medium hover:bg-[var(--gold)] transition-colors cursor-pointer">
                  保存到本地
                </button>
              </div>

              {/* Logo 上传 */}
              <div className="border-t border-[var(--border)] pt-3 mt-2">
                <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">公司 Logo</p>
                {companyLogoPreview && (
                  <img src={companyLogoPreview} className="h-12 mb-2 object-contain rounded border border-[var(--border)]" alt="logo" />
                )}
                <input type="file" accept="image/jpeg,image/png,image/gif" onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;
                  const formData = new FormData();
                  formData.append('file', file);
                  try {
                    const r = await fetch(`${API_BASE}/api/company/logo`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` },
                      body: formData,
                    });
                    const d = await r.json();
                    if (r.ok) setCompanyLogoPreview(`${API_BASE}/api/images?path=${encodeURIComponent(d.path)}`);
                  } catch (e) {}
                }} className="text-sm" />
              </div>

              {companyMsg && <p className="text-xs text-[var(--success)]">{companyMsg}</p>}
              <button onClick={async () => {
                const body = new URLSearchParams();
                body.append('config', JSON.stringify({
                  name: companyName, name_en: companyNameEn,
                  address: companyAddress, address_en: companyAddressEn,
                  city: companyCity, tel: companyPhone,
                  email: companyEmail, website: companyWebsite,
                  contact_person: companyContact,
                }));
                try {
                  const r = await fetch(`${API_BASE}/api/template/save`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` },
                    body
                  });
                  if (!r.ok) throw new Error('保存失败');
                  setCompanyMsg('保存成功');
                  setTimeout(() => setCompanyMsg(''), 3000);
                } catch (e) { setCompanyMsg('保存失败'); }
              }} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors cursor-pointer">
                保存
              </button>
            </div>
          )}
        </div>

        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <button
            onClick={() => setShowPwChange(!showPwChange)}
            className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-[var(--warm-white)] transition-colors cursor-pointer"
          >
            <span className="text-sm font-medium text-[var(--navy)]">修改密码</span>
            <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${showPwChange ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showPwChange && (
            <form onSubmit={handleChangePw} className="px-5 pb-5 border-t border-[var(--border)] pt-4 space-y-3">
              <div>
                <label className="text-xs font-medium text-[var(--text-secondary)]">旧密码</label>
                <div className="relative mt-1">
                  <input type={showOldPw ? 'text' : 'password'} value={oldPw} onChange={e => setOldPw(e.target.value)} placeholder="输入旧密码" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" />
                  <button type="button" onClick={() => setShowOldPw(!showOldPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                    {showOldPw ? '隐藏' : '显示'}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-[var(--text-secondary)]">新密码</label>
                <div className="relative mt-1">
                  <input type={showNewPw ? 'text' : 'password'} value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="输入新密码" className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" />
                  <button type="button" onClick={() => setShowNewPw(!showNewPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                    {showNewPw ? '隐藏' : '显示'}
                  </button>
                </div>
              </div>
              {pwMsg && (
                <p className={`text-xs ${pwMsgType === 'success' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
                  {pwMsg}
                </p>
              )}
              <button type="submit" disabled={pwLoading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50 cursor-pointer">
                {pwLoading ? '保存中...' : '保存'}
              </button>
            </form>
          )}
        </div>

        {/* 文档模板 */}
        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <div className="px-5 py-3 border-b border-[var(--border)]">
            <p className="text-sm font-medium text-[var(--navy)]">文档模板</p>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">上传 .xlsx 模板，生成文档时将按模板格式输出。不传则用内置格式。</p>
          </div>
          <div className="px-5 py-3 space-y-3">
            {[
              ['quotation', '📊', 'Excel报价单'],
              ['pi', '📋', '形式发票 PI'],
              ['packing', '📦', '装箱单'],
              ['invoice', '🧾', '商业发票'],
            ].map(([type, icon, label]) => (
              <div key={type} className="flex items-center justify-between py-1" id={`tmpl-${type}`}>
                <span className="text-sm"><span>{icon}</span> {label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-secondary)]" id={`tmpl-status-${type}`}>检查中...</span>
                  <input type="file" accept=".xlsx" className="hidden" id={`tmpl-file-${type}`}
                    onChange={async (e) => {
                      const f = e.target.files?.[0]; if (!f) return;
                      const fd = new FormData(); fd.append('file', f);
                      try {
                        const r = await fetch(`${API_BASE}/api/template/document/${type}`, {
                          method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }, body: fd
                        });
                        if (r.ok) { const el = document.getElementById(`tmpl-status-${type}`); if (el) el.textContent = '✅ 已上传'; }
                      } catch(e) {}
                    }} />
                  <button onClick={() => { const el = document.getElementById(`tmpl-file-${type}`); if (el) el.click(); }}
                    className="px-3 py-1 rounded-lg border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:bg-gray-50 transition-colors cursor-pointer">
                    选择文件
                  </button>
                  <button onClick={async () => {
                    try {
                      const r = await fetch(`${API_BASE}/api/template/document/${type}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` } });
                      if (r.ok) { const el = document.getElementById(`tmpl-status-${type}`); if (el) el.textContent = '未上传'; }
                    } catch(e) {}
                  }} className="text-xs text-[var(--error)] hover:underline cursor-pointer">删除</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {user.tier !== 'pro' && (
          <a href="/pricing"
             className="block mt-4 text-center py-2.5 rounded-lg bg-[var(--gold)] text-[var(--navy)] font-semibold text-sm hover:bg-[var(--gold-light)] transition-colors">
            升级专业版
          </a>
        )}
      </section>

      <footer className="border-t border-[var(--border)] py-6 px-6 text-center text-xs text-[var(--text-secondary)]">
        报价整合工具 · 专为外贸 SOHO 设计
      </footer>
    </div>
  );
}
