'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isLoggedIn, getStoredUser, clearAuth } from '@/lib/auth';
import API_BASE from '@/lib/api';
import { useLocale, t } from '@/lib/i18n';

export default function AccountPage() {
  const router = useRouter();
  const { locale, ready } = useLocale();
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
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json()).then(setUsage).catch(e => console.error('Failed to load usage:', e));
    fetch(`${API_BASE}/api/template?user_id=${getStoredUser()?.id || 'local'}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
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
    ['quotation','pi','packing','invoice'].forEach(async (type) => {
      try {
        const r = await fetch(`${API_BASE}/api/template/document/${type}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        const d = await r.json();
        const el = document.getElementById(`tmpl-status-${type}`);
        if (el) el.textContent = d.exists ? `✅ ${t('account.uploaded', locale)} (${(d.size/1024).toFixed(0)}KB)` : t('account.notUploaded', locale);
      } catch(e) {}
    });
    try {
      fetch(`${API_BASE}/api/bank/load`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      }).then(r => r.json()).then(stored => {
        if (stored.beneficiary) setBankBeneficiary(stored.beneficiary);
        if (stored.bank_name) setBankName(stored.bank_name);
        if (stored.bank_address) setBankAddress(stored.bank_address);
        if (stored.account_no) setBankAccount(stored.account_no);
        if (stored.swift_code) setBankSwift(stored.swift_code);
      }).catch(() => {});
    } catch (e) {}
  }, [router]);

  if (!ready) return null;

  const handleLogout = () => { clearAuth(); router.push('/'); };

  const handleChangePw = async (e) => {
    e.preventDefault();
    setPwMsg('');
    if (!oldPw || !newPw) { setPwMsg(t('account.fillAllFields', locale)); setPwMsgType('error'); return; }
    if (newPw.length < 6) { setPwMsg(t('account.passwordMinLength', locale)); setPwMsgType('error'); return; }
    setPwLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('old_password', oldPw);
      body.append('new_password', newPw);
      const res = await fetch(`${API_BASE}/api/auth/change-password`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t('account.passwordError', locale));
      setPwMsg(t('account.passwordChanged', locale));
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
        <a href="/" className="text-xl font-bold text-[var(--navy)] tracking-tight">{t('nav.title', locale)}</a>
        <div className="flex items-center gap-5 text-sm">
          <a href="/" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">{t('nav.home', locale)}</a>
          <a href="/how-it-works" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">{t('nav.howItWorks', locale)}</a>
          <a href="/pricing" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">{t('nav.pricing', locale)}</a>
          <a href="/workspace" className="text-[var(--text-secondary)] hover:text-[var(--navy)] transition-colors">{t('nav.workspace', locale)}</a>
          <div className="relative group">
            <button className="flex items-center gap-1 text-[var(--navy)] font-medium cursor-pointer">
              {user.username} <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white border border-[var(--border)] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
              <span className="block px-4 py-2 text-sm font-medium text-[var(--navy)] bg-gray-50 rounded-t-lg">{t('account.title', locale)}</span>
              <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-[var(--error)] hover:bg-red-50 rounded-b-lg cursor-pointer">{t('account.logout', locale)}</button>
            </div>
          </div>
        </div>
      </nav>

      <section className="flex-1 max-w-md mx-auto w-full px-6 pt-16">
        <h1 className="text-2xl font-bold text-[var(--navy)] mb-6">{t('account.title', locale)}</h1>

        <div className="border border-[var(--border)] rounded-xl p-6 bg-[var(--surface)] space-y-4">
          <div className="flex justify-between text-sm">
            <span className="text-[var(--text-secondary)]">{t('auth.username', locale)}</span>
            <span className="font-medium text-[var(--navy)]">{user.username}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[var(--text-secondary)]">{t('account.tier', locale)}</span>
            <span className={`font-medium ${user.tier === 'pro' ? 'text-[var(--gold)]' : 'text-[var(--text-secondary)]'}`}>
              {user.tier === 'pro' ? t('account.tierPro', locale) : t('account.tierFree', locale)}
            </span>
          </div>
          {usage && (
            <div className="flex justify-between text-sm">
              <span className="text-[var(--text-secondary)]">{t('account.monthlyUploads', locale)}</span>
              <span className="font-medium text-[var(--navy)]">{usage.upload_count} / {usage.limit} {t('account.times', locale)}</span>
            </div>
          )}
        </div>

        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <button
            onClick={() => setShowCompany(!showCompany)}
            className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-[var(--warm-white)] transition-colors cursor-pointer"
          >
            <span className="text-sm font-medium text-[var(--navy)]">{t('account.company', locale)}</span>
            <span className="text-xs text-[var(--text-secondary)]">{t('account.companyHint', locale)}</span>
            <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${showCompany ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showCompany && (
            <div className="px-5 pb-5 border-t border-[var(--border)] pt-4 space-y-3">
              <input type="text" value={companyName} onChange={e => setCompanyName(e.target.value)}
                placeholder={t('account.companyNameZh', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyNameEn} onChange={e => setCompanyNameEn(e.target.value)}
                placeholder={t('account.companyNameEn', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyAddress} onChange={e => setCompanyAddress(e.target.value)}
                placeholder={t('account.companyAddressZh', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyAddressEn} onChange={e => setCompanyAddressEn(e.target.value)}
                placeholder={t('account.companyAddressEn', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyCity} onChange={e => setCompanyCity(e.target.value)}
                placeholder={t('account.companyCity', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <div className="grid grid-cols-2 gap-3">
                <input type="text" value={companyPhone} onChange={e => setCompanyPhone(e.target.value)}
                  placeholder={t('account.companyPhone', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
                <input type="text" value={companyEmail} onChange={e => setCompanyEmail(e.target.value)}
                  placeholder={t('account.companyEmail', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              </div>
              <input type="text" value={companyWebsite} onChange={e => setCompanyWebsite(e.target.value)}
                placeholder={t('account.companyWebsite', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
              <input type="text" value={companyContact} onChange={e => setCompanyContact(e.target.value)}
                placeholder={t('account.companyContact', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />

              <div className="border-t border-[var(--border)] pt-3 mt-2">
                <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">{t('account.bankInfoLabel', locale)}</p>
                <p className="text-[10px] text-gray-400 mb-2">{t('account.bankInfoHint', locale)}</p>
                <input type="text" value={bankBeneficiary} onChange={e => setBankBeneficiary(e.target.value)}
                  placeholder={t('account.bankBeneficiary', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankName} onChange={e => setBankName(e.target.value)}
                  placeholder={t('account.bankName', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankAddress} onChange={e => setBankAddress(e.target.value)}
                  placeholder={t('account.bankAddress', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankAccount} onChange={e => setBankAccount(e.target.value)}
                  placeholder={t('account.bankAccount', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] mb-2" />
                <input type="text" value={bankSwift} onChange={e => setBankSwift(e.target.value)}
                  placeholder={t('account.bankSwift', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)]" />
                {bankMsg && <p className="text-xs text-[var(--success)] mt-1">{bankMsg}</p>}
                <button onClick={async () => {
                  setBankMsg('');
                  try {
                    const b = new URLSearchParams();
                    b.append('beneficiary', bankBeneficiary);
                    b.append('bank_name', bankName);
                    b.append('bank_address', bankAddress);
                    b.append('account_no', bankAccount);
                    b.append('swift_code', bankSwift);
                    const res = await fetch(`${API_BASE}/api/bank/save`, {
                      method: 'POST', body: b,
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/x-www-form-urlencoded' }
                    });
                    if (res.ok) {
                      setBankMsg(t('account.bankSaved', locale));
                      setTimeout(() => setBankMsg(''), 3000);
                    }
                  } catch (e) {}
                }} className="mt-2 w-full py-2 rounded-lg border border-[var(--gold)] text-[var(--navy)] text-sm font-medium hover:bg-[var(--gold)] transition-colors cursor-pointer">
                  {t('account.bankSaveLocal', locale)}
                </button>
              </div>

              <div className="border-t border-[var(--border)] pt-3 mt-2">
                <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">{t('account.companyLogo', locale)}</p>
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
                  if (!r.ok) throw new Error(t('account.companySaveError', locale));
                  setCompanyMsg(t('account.companySaved', locale));
                  setTimeout(() => setCompanyMsg(''), 3000);
                } catch (e) { setCompanyMsg(t('account.companySaveError', locale)); }
              }} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors cursor-pointer">
                {t('account.companySave', locale)}
              </button>
            </div>
          )}
        </div>

        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <button
            onClick={() => setShowPwChange(!showPwChange)}
            className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-[var(--warm-white)] transition-colors cursor-pointer"
          >
            <span className="text-sm font-medium text-[var(--navy)]">{t('account.password', locale)}</span>
            <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${showPwChange ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showPwChange && (
            <form onSubmit={handleChangePw} className="px-5 pb-5 border-t border-[var(--border)] pt-4 space-y-3">
              <div>
                <label className="text-xs font-medium text-[var(--text-secondary)]">{t('account.passwordCurrent', locale)}</label>
                <div className="relative mt-1">
                  <input type={showOldPw ? 'text' : 'password'} value={oldPw} onChange={e => setOldPw(e.target.value)} placeholder={t('account.passwordCurrentPlaceholder', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" />
                  <button type="button" onClick={() => setShowOldPw(!showOldPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                    {showOldPw ? t('account.hide', locale) : t('account.show', locale)}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-[var(--text-secondary)]">{t('account.passwordNew', locale)}</label>
                <div className="relative mt-1">
                  <input type={showNewPw ? 'text' : 'password'} value={newPw} onChange={e => setNewPw(e.target.value)} placeholder={t('account.passwordNewPlaceholder', locale)} className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--navy)] pr-9" />
                  <button type="button" onClick={() => setShowNewPw(!showNewPw)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--navy)] cursor-pointer text-xs">
                    {showNewPw ? t('account.hide', locale) : t('account.show', locale)}
                  </button>
                </div>
              </div>
              {pwMsg && (
                <p className={`text-xs ${pwMsgType === 'success' ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
                  {pwMsg}
                </p>
              )}
              <button type="submit" disabled={pwLoading} className="w-full py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50 cursor-pointer">
                {pwLoading ? t('account.saving', locale) : t('account.passwordChange', locale)}
              </button>
            </form>
          )}
        </div>

        <div className="mt-4 border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <div className="px-5 py-3 border-b border-[var(--border)]">
            <p className="text-sm font-medium text-[var(--navy)]">{t('account.documents', locale)}</p>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">{t('account.documentTip', locale)}</p>
          </div>
          <div className="px-5 py-3 space-y-3">
              {[
                ['quotation', '📊', t('account.documentQuotation', locale)],
                ['pi', '📋', t('account.documentPI', locale)],
                ['packing', '📦', t('account.documentPacking', locale)],
                ['invoice', '🧾', t('account.documentInvoice', locale)],
              ].map(([type, icon, label]) => (
              <div key={type} className="flex items-center justify-between py-1" id={`tmpl-${type}`}>
                <span className="text-sm"><span>{icon}</span> {label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-secondary)]" id={`tmpl-status-${type}`}>{t('account.checking', locale)}</span>
                  <input type="file" accept=".xlsx" className="hidden" id={`tmpl-file-${type}`}
                    onChange={async (e) => {
                      const f = e.target.files?.[0]; if (!f) return;
                      const fd = new FormData(); fd.append('file', f);
                      try {
                        const r = await fetch(`${API_BASE}/api/template/document/${type}`, {
                          method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }, body: fd
                        });
                        if (r.ok) { const el = document.getElementById(`tmpl-status-${type}`); if (el) el.textContent = `✅ ${t('account.uploaded', locale)}`; }
                      } catch(e) {}
                    }} />
                  <button onClick={() => { const el = document.getElementById(`tmpl-file-${type}`); if (el) el.click(); }}
                    className="px-3 py-1 rounded-lg border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:bg-gray-50 transition-colors cursor-pointer">
                    {t('account.selectFile', locale)}
                  </button>
                  <button onClick={async () => {
                    try {
                      const r = await fetch(`${API_BASE}/api/template/document/${type}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` } });
                      if (r.ok) { const el = document.getElementById(`tmpl-status-${type}`); if (el) el.textContent = t('account.notUploaded', locale); }
                    } catch(e) {}
                  }} className="text-xs text-[var(--error)] hover:underline cursor-pointer">{t('account.delete', locale)}</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {user.tier !== 'pro' && (
          <a href="/pricing"
             className="block mt-4 text-center py-2.5 rounded-lg bg-[var(--gold)] text-[var(--navy)] font-semibold text-sm hover:bg-[var(--gold-light)] transition-colors">
            {t('account.upgrade', locale)}
          </a>
        )}
      </section>

      <footer className="border-t border-[var(--border)] py-6 px-6 text-center text-xs text-[var(--text-secondary)]">
        {t('footer.copyright', locale)}
      </footer>
    </div>
  );
}
