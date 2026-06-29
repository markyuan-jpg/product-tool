'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import API_BASE from '@/lib/api';
import { isLoggedIn, getStoredUser, getToken } from '@/lib/auth';
import { friendlyError } from '@/lib/errors';
import { useLocale, t } from '@/lib/i18n';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

const features = [
  { icon: '\uD83D\uDD0D', key: 'autoParse' },
  { icon: '\uD83D\uDCB0', key: 'smartQuote' },
  { icon: '\uD83D\uDCC4', key: 'fullDocs' },
];

export default function Home() {
  const { locale, ready } = useLocale();
  const [dragOver, setDragOver] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [showCompanyPanel, setShowCompanyPanel] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [companyContact, setCompanyContact] = useState('');
  const [companyPhone, setCompanyPhone] = useState('');
  const [templateUploading, setTemplateUploading] = useState(false);
  const [authUser, setAuthUser] = useState(null);
  const [failedImages, setFailedImages] = useState(new Set());
  const [fileEntries, setFileEntries] = useState([]);
  const [checkedFiles, setCheckedFiles] = useState(new Set());
  const MAX_FREE_FILES = 3;
  const uploadLocked = fileEntries.length >= MAX_FREE_FILES;
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const processingRef = useRef(false);
  const activeProducts = fileEntries.reduce((arr, entry, idx) => {
    if (checkedFiles.has(idx)) arr.push(...(entry.products || []));
    return arr;
  }, []);
  const allChecked = fileEntries.length > 0 && checkedFiles.size === fileEntries.length;

  useEffect(() => { if (isLoggedIn()) setAuthUser(getStoredUser()); }, []);

  // SEO — set page title and meta description dynamically
  useEffect(() => {
    if (!ready) return;
    document.title = locale === 'zh'
      ? 'QuoteFlow - 产品报价单在线生成工具'
      : 'QuoteFlow - Product Quotation Generator';
    const desc = locale === 'zh'
      ? '上传 Excel / PDF / Word 产品文件，自动解析生成报价单。免费使用。'
      : 'Upload Excel, PDF, or Word product files. Auto-parse and generate quotations. Free to use.';
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) { meta = document.createElement('meta'); meta.name = 'description'; document.head.appendChild(meta); }
    meta.setAttribute('content', desc);
  }, [locale, ready]);

  const handleDrag = useCallback((e) => { e.preventDefault(); e.stopPropagation(); }, []);
  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
    if (uploadLocked) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [uploadLocked, fileEntries.length]);

  const handleClick = () => { if (!uploadLocked) inputRef.current?.click(); };
  const handleFileSelect = (e) => { const file = e.target.files[0]; if (file) handleFile(file); };
  const handleAddFileClick = () => fileInputRef.current?.click();
  const handleAddFileSelect = (e) => { const file = e.target.files[0]; if (file) handleFile(file); };

  const handleFile = async (file) => {
    if (processingRef.current || fileEntries.length >= MAX_FREE_FILES) return;
    processingRef.current = true;
    const valid = ['.xlsx', '.xls', '.pdf', '.docx'].some(ext => file.name.toLowerCase().endsWith(ext));
    if (!valid) { alert('仅支持 .xlsx / .xls / .pdf / .docx'); processingRef.current = false; return; }
    setParsing(true); setParseError(null);
    try {
      const fd = new FormData(); fd.append('file', file);
      const ac = new AbortController(); const tid = setTimeout(() => ac.abort(), 60000);
      const res = await fetch(API_BASE + '/api/parse', { method: 'POST', body: fd, signal: ac.signal });
      clearTimeout(tid);
      if (!res.ok) { const e = await res.json().catch(() => ({ detail: '解析失败' })); throw new Error(e.detail || '服务器错误 ' + res.status); }
      const data = await res.json();
      setFileEntries(prev => [...prev, { name: file.name, products: data.products || [], dedupCount: data.dedup || null }]);
      setCheckedFiles(prev => { const next = new Set(prev); next.add(prev.size); return next; });
      setParsing(false);
    } catch (err) { setParseError(friendlyError(err)); setParsing(false); }
    processingRef.current = false;
  };

  // Demo: 无需上传即可预览效果
  const demoProducts = [
    { model: 'BT-001', name_zh: '蓝牙耳机', spec_zh: '蓝牙5.3 / 续航8h / IPX5防水 / Type-C充电', price_rmb: 45.00, currency: 'CNY', category: '电子产品' },
    { model: 'BP-200', name_zh: '移动电源 20000mAh', spec_zh: '22.5W快充 / USB-C+双USB-A / LED电量显示 / 20000mAh', price_rmb: 68.00, currency: 'CNY', category: '电子产品' },
    { model: 'WK-500', name_zh: '智能手表', spec_zh: '1.43英寸AMOLED / 心率血氧监测 / IP68防水 / 14天续航', price_rmb: 129.00, currency: 'CNY', category: '智能穿戴' },
    { model: 'SP-100', name_zh: '蓝牙音箱', spec_zh: '20W输出 / IPX7防水 / TWS串联 / 12h续航', price_rmb: 89.00, currency: 'CNY', category: '电子产品' },
    { model: 'CL-300', name_zh: 'LED台灯', spec_zh: '无级调光 / 色温2700-6500K / USB供电 / 折叠便携', price_rmb: 35.00, currency: 'CNY', category: '家居用品' },
  ];
  const handleDemo = () => {
    setFileEntries([{ name: locale === 'zh' ? '示例产品.xlsx' : 'demo_products.xlsx', products: demoProducts, dedupCount: null }]);
    setCheckedFiles(new Set([0]));
  };

  const toggleFile = (idx) => {
    setCheckedFiles(prev => {
      if (prev.has(idx) && prev.size <= 1) return prev;
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
    setFailedImages(new Set());
  };
  const toggleAll = () => {
    setCheckedFiles(allChecked ? new Set([0]) : new Set(fileEntries.map((_, i) => i)));
    setFailedImages(new Set());
  };
  const handleGenerateQuotation = () => { if (activeProducts.length > 0) setShowCompanyPanel(true); };

  const confirmQuotation = async () => {
    setShowCompanyPanel(false); setGenerating(true);
    try {
      const b = new URLSearchParams();
      b.append('products', JSON.stringify(activeProducts));
      b.append('lang', 'bilingual');
      if (companyName) b.append('company_name', companyName);
      if (companyContact) b.append('company_contact', companyContact);
      if (companyPhone) b.append('company_phone', companyPhone);
      const ac = new AbortController();
      const tid = setTimeout(() => ac.abort(), 120000);
      const r = await fetch(API_BASE + '/api/quotation', { method: 'POST', body: b, signal: ac.signal });
      clearTimeout(tid);
      if (!r.ok) throw new Error('生成失败');
      const ct = r.headers.get('content-type') || '';
      if (ct.includes('json')) {
        const data = await r.json();
        if (data.id) {
          const token = getToken();
          const dlR = await fetch(API_BASE + '/api/quotations/' + data.id + '/download', {
            headers: token ? { 'Authorization': 'Bearer ' + token } : {}
          });
          if (dlR.ok) {
            const blob = await dlR.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = data.name || '报价单_' + Date.now() + '.xlsx'; document.body.appendChild(a); a.click(); document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }
        }
      } else {
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = '报价单_' + Date.now() + '.xlsx'; document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) { alert('生成报价单失败：' + friendlyError(err)); }
    setGenerating(false);
  };

  const handleTemplateUpload = async (file) => {
    setTemplateUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const ac = new AbortController(); const tid = setTimeout(() => ac.abort(), 30000);
      const r = await fetch(API_BASE + '/api/template/upload', { method: 'POST', body: fd, signal: ac.signal });
      clearTimeout(tid);
      if (!r.ok) throw new Error('模板解析失败');
      const d = await r.json();
      if (d.company?.company_name) setCompanyName(d.company.company_name);
      if (d.company?.contact) setCompanyContact(d.company.contact);
      if (d.company?.phone) setCompanyPhone(d.company.phone);
    } catch (err) { alert(friendlyError(err)); }
    setTemplateUploading(false);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Nav current="home" />

      <section className="flex-1 px-6 pt-12 pb-20 max-w-5xl mx-auto w-full">
        {/* HERO */}
        <div className="text-center mb-10 hero-gradient rounded-2xl py-12 px-6 -mx-6">
          <h1 className="text-4xl sm:text-5xl font-bold text-[var(--navy)] leading-tight mb-3">
            {locale === 'zh' ? <>上传文件，<span className="text-[var(--gold)]">30秒</span>生成报价单</> : t('home.hero.title', locale)}
          </h1>
          <p className="text-base text-[var(--text-secondary)] mb-6">{t('home.hero.subtitle', locale)}</p>
          <div onDragOver={handleDrag} onDragEnter={() => setDragOver(true)} onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop} onClick={handleClick}
            className={'w-full max-w-xl mx-auto border-2 border-dashed rounded-2xl p-10 transition-all duration-300 cursor-pointer ' + (dragOver ? 'border-[var(--gold)] bg-[var(--gold)]/5 scale-[1.02]' : 'border-[var(--border)] hover:border-[var(--navy)] hover:bg-gray-50') + (uploadLocked ? ' opacity-60' : '')}>
            <input ref={inputRef} type="file" accept=".xlsx,.xls,.pdf,.docx" onChange={handleFileSelect} className="hidden" />
            {parsing ? (
              <div className="flex flex-col items-center gap-3"><div className="w-9 h-9 border-[2.5px] border-[var(--navy)] border-t-transparent rounded-full animate-spin" /><p className="text-sm">{t('home.hero.parsing', locale)}</p></div>
            ) : uploadLocked ? (
              <div className="flex flex-col items-center gap-2"><span className="text-3xl">&#10003;</span><p className="text-sm font-medium text-[var(--navy)]">{t('home.hero.maxReached', locale)}</p><a href="/register" className="px-5 py-2 rounded-lg bg-[var(--navy)] text-white text-xs font-medium hover:bg-[var(--navy-light)]">{t('home.hero.freeRegister', locale)}</a></div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <svg className="w-10 h-10 text-[var(--navy-light)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-sm font-medium text-[var(--navy)]">{t('home.hero.dragDrop', locale)}</p>
                <p className="text-xs text-[var(--text-secondary)]">{t('home.hero.supportedFormats', locale).replace('{count}', fileEntries.length).replace('{limit}', MAX_FREE_FILES)}</p>
              </div>
            )}
          </div>
          {!uploadLocked && (
            <button onClick={handleDemo}
              className="mt-4 px-5 py-2 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 transition-colors cursor-pointer">
              {locale === 'zh' ? '🎯 试试 Demo（无需上传）' : '🎯 Try Demo (No Upload Needed)'}
            </button>
          )}
        </div>

        {/* Error */}
        {parseError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
            <span className="text-red-500 font-bold text-lg">&#9888;</span>
            <div className="flex-1"><p className="text-sm font-medium text-red-700">{t('home.parseError', locale)}</p><p className="text-xs text-red-500">{parseError}</p></div>
            <button onClick={() => setParseError(null)} className="text-xs text-red-500 underline cursor-pointer">{t('home.retry', locale)}</button>
          </div>
        )}

        {/* 3 Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-10">
          {features.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="fc-icon">{f.icon}</div>
              <h3>{t(`home.features.${f.key}.title`, locale)}</h3>
              <ul>{[0,1,2].map(j => <li key={j}>{t(`home.features.${f.key}.items.${j}`, locale)}</li>)}</ul>
            </div>
          ))}
        </div>

        {/* After-upload panels */}
        {fileEntries.length > 0 && (
          <div className="space-y-6">
            {/* File tabs with multi-select */}
            <div className="flex items-center gap-2 overflow-x-auto thin-scroll">
              {fileEntries.map((entry, idx) => (
                <label key={idx} className={'file-tab cursor-pointer ' + (checkedFiles.has(idx) ? 'active' : '')}>
                  <input type="checkbox" checked={checkedFiles.has(idx)} onChange={() => toggleFile(idx)} className="mr-1.5" />
                  {entry.name} <span className="text-xs opacity-60 ml-1">({(entry.products || []).length})</span>
                </label>
              ))}
              {fileEntries.length > 1 && (
                <label className="file-tab-add cursor-pointer">
                  <input type="checkbox" checked={allChecked} onChange={toggleAll} className="mr-1" />
                  {t('home.selectAll', locale)}
                </label>
              )}
              {!uploadLocked && <button onClick={handleAddFileClick} className="file-tab-add" title={t('home.addFile', locale)}>+</button>}
              <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.pdf,.docx" onChange={handleAddFileSelect} className="hidden" />
            </div>

            {/* Count + CTA */}
            {activeProducts.length > 0 && (
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-[var(--navy)]">
                  {checkedFiles.size > 1 ? `${checkedFiles.size} ${t('home.filesSelected', locale)} · ` : ''}{activeProducts.length} {t('home.productsTotal', locale)}
                </p>
                <button onClick={handleGenerateQuotation} disabled={generating}
                  className="px-4 py-2 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 disabled:opacity-50 cursor-pointer">
                  {generating ? t('home.generating', locale) : t('home.generateQuote', locale)}
                </button>
              </div>
            )}

            {/* Panel 1 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128269;</div><div className="panel-title">{t('home.features.autoParse.title', locale)}</div>
                  <p>{t('home.features.autoParse.items.0', locale)}，{t('home.features.autoParse.items.1', locale)}</p>
                </div>
                <div className="scenario-content flex-1">
                  {activeProducts.length > 0 ? (
                    <div className="max-h-64 overflow-auto thin-scroll">
                      <table className="prod-table">
                        <thead><tr><th></th><th>{t('home.model', locale)}</th><th>{t('home.name', locale)}</th><th>{t('home.spec', locale)}</th><th>{t('home.price', locale)}</th></tr></thead>
                        <tbody>{activeProducts.slice(0, 50).map((p, i) => (
                          <tr key={i}>
                            <td className="w-10 h-10 p-1">
                              {p._image_path && !failedImages.has(i) ? (
                                <img src={API_BASE + '/api/images/?path=' + encodeURIComponent(p._image_path)} alt="" className="w-8 h-8 object-cover rounded"
                                  loading="lazy" onError={() => setFailedImages(prev => { const n = new Set(prev); n.add(i); return n; })} />
                              ) : <span className="text-xs text-gray-300">—</span>}
                            </td>
                            <td className="font-mono text-[0.75rem] max-w-[100px] overflow-hidden text-ellipsis whitespace-nowrap" title={p.model}>{p.model || '-'}</td>
                            <td className="max-w-[140px] overflow-hidden text-ellipsis whitespace-nowrap" title={p.name_zh || p.name_en}>{p.name_zh || p.name_en || '-'}</td>
                            <td className="max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap" title={p.spec_zh || p.spec_en}>{p.spec_zh || p.spec_en || '-'}</td>
                            <td className="font-medium">{p.currency === 'USD' ? '$' : '¥'}{p.price_rmb || '-'}</td></tr>
                        ))}</tbody>
                      </table>
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">{t('home.features.autoParse.items.0', locale)}</p></div>}
                </div>
              </div>
            </div>

            {/* Panel 2 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128176;</div><div className="panel-title">{t('home.features.smartQuote.title', locale)}</div>
                  <p>{t('home.features.smartQuote.items.0', locale)}、{t('home.features.smartQuote.items.1', locale)}</p>
                </div>
                <div className="scenario-content flex-1">
                  {activeProducts.length > 0 ? (
                    <div className="prod-cards max-h-64 overflow-auto thin-scroll">
                      {activeProducts.slice(0, 30).map((p, i) => (
                        <div key={i} className="prod-card">
                          <div className="prod-card-img">
                            {p._image_path && !failedImages.has(i) ? (
                              <img src={API_BASE + '/api/images/?path=' + encodeURIComponent(p._image_path)} alt="" className="w-full h-full object-cover"
                                onError={() => setFailedImages(prev => { const n = new Set(prev); n.add(i); return n; })} />
                            ) : <span>&#128230;</span>}
                          </div>
                          <div className="prod-card-body"><div className="name">{p.name_zh || p.name_en || p.model || '-'}</div>
                          <div className="model">{p.model || ''}</div><div className="qty">{t('home.productsFound', locale).replace('{count}', '').replace('{dedup}', '')}{p.quantity || 1}</div></div>
                        </div>
                      ))}
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">{t('home.features.smartQuote.items.0', locale)}</p></div>}
                </div>
              </div>
            </div>

            {/* Panel 3 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128196;</div><div className="panel-title">{t('home.features.fullDocs.title', locale)}</div>
                  <p>{t('home.features.fullDocs.items.0', locale)}</p>
                </div>
                <div className="scenario-content flex-1">
                  {activeProducts.length > 0 ? (
                    <div className="doc-list">
                      {[
                        ['excel', t('home.features.fullDocs.items.0', locale), 'check'],
                        ['pdf', t('home.features.fullDocs.items.1', locale), 'check'],
                        ['pi', t('home.features.fullDocs.items.2', locale), 'pro'],
                      ].map(([cls, label, badge], i) => (
                        <div key={i} className="doc-item">
                          <div className={'doc-icon ' + cls}>&#128196;</div>
                          <span className="doc-label">{label}</span>
                          {badge === 'check' ? <span className="doc-check">&#10003;</span> : <span className="doc-badge pro">Pro</span>}
                        </div>
                      ))}
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">{t('home.features.fullDocs.items.0', locale)}</p></div>}
                </div>
              </div>
            </div>
          </div>
        )}

      </section>

      {/* Company info modal */}
      {showCompanyPanel && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4" onClick={() => setShowCompanyPanel(false)}>
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-bold text-[var(--navy)] mb-4">{t('home.companyPanel.title', locale)}</h3>
            <div className="space-y-3">
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">{t('home.companyPanel.companyName', locale)}</label>
              <input value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder={t('home.companyPanel.placeholderName', locale)} className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">{t('home.companyPanel.contact', locale)}</label>
              <input value={companyContact} onChange={e => setCompanyContact(e.target.value)} placeholder={t('home.companyPanel.placeholderContact', locale)} className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">{t('home.companyPanel.phone', locale)}</label>
              <input value={companyPhone} onChange={e => setCompanyPhone(e.target.value)} placeholder={t('home.companyPanel.placeholderPhone', locale)} className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div className="border-t pt-3 mt-3">
                <p className="text-xs text-[var(--text-secondary)] mb-2">{t('home.companyPanel.uploadTemplate', locale)}</p>
                <label className="block w-full py-2 text-center rounded-lg border text-sm text-[var(--text-secondary)] hover:bg-gray-50 cursor-pointer">
                  {templateUploading ? t('home.companyPanel.parsing', locale) : t('home.companyPanel.uploadTemplateBtn', locale)}
                  <input type="file" accept=".xlsx,.xls" className="hidden" onChange={e => { if (e.target.files[0]) handleTemplateUpload(e.target.files[0]); }} />
                </label>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCompanyPanel(false)} className="flex-1 py-2 rounded-lg border text-sm cursor-pointer">{t('home.companyPanel.cancel', locale)}</button>
              <button onClick={confirmQuotation} className="flex-1 py-2 rounded-lg bg-[var(--gold)] text-white text-sm font-medium cursor-pointer">{t('home.companyPanel.generate', locale)}</button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
