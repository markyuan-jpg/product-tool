'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import API_BASE from '@/lib/api';
import { isLoggedIn, getStoredUser } from '@/lib/auth';
import { friendlyError } from '@/lib/errors';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

const features = [
  {
    icon: '\uD83D\uDD0D', title: '自动解析',
    items: ['自动提取产品型号、规格和价格', '支持 Excel / PDF / Word 等常见格式', '多个文件自动去重整合'],
  },
  {
    icon: '\uD83D\uDCB0', title: '智能报价',
    items: ['自动为每个产品匹配图片', '支持中英双语报价', 'EXW / FOB / CIF 贸易术语'],
  },
  {
    icon: '\uD83D\uDCC4', title: '全部出单',
    items: ['Excel 报价单（含产品图片）', 'PDF 报价单 / 形式发票 PI', '装箱单 + 商业发票'],
  },
];

export default function Home() {
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
  const [activeFileIdx, setActiveFileIdx] = useState(-1);
  const MAX_FREE_FILES = 3;
  const uploadLocked = fileEntries.length >= MAX_FREE_FILES;
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const processingRef = useRef(false);
  const activeProducts = activeFileIdx >= 0 && activeFileIdx < fileEntries.length
    ? fileEntries[activeFileIdx].products : [];

  useEffect(() => { if (isLoggedIn()) setAuthUser(getStoredUser()); }, []);

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
      setActiveFileIdx(prev => prev === -1 ? 0 : prev);
      setParsing(false);
    } catch (err) { setParseError(friendlyError(err)); setParsing(false); }
    processingRef.current = false;
  };

  const switchFile = (idx) => { setActiveFileIdx(idx); setFailedImages(new Set()); };
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
      const r = await fetch(API_BASE + '/api/quotation', { method: 'POST', body: b });
      if (!r.ok) throw new Error('生成失败');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = '报价单_' + Date.now() + '.xlsx'; a.click();
      URL.revokeObjectURL(url);
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
            上传文件，<span className="text-[var(--gold)]">30秒</span>生成报价单
          </h1>
          <p className="text-base text-[var(--text-secondary)] mb-6">Excel / PDF / Word 拖进来，自动解析出产品</p>
          <div onDragOver={handleDrag} onDragEnter={() => setDragOver(true)} onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop} onClick={handleClick}
            className={'w-full max-w-xl mx-auto border-2 border-dashed rounded-2xl p-10 transition-all duration-300 cursor-pointer ' + (dragOver ? 'border-[var(--gold)] bg-[var(--gold)]/5 scale-[1.02]' : 'border-[var(--border)] hover:border-[var(--navy)] hover:bg-gray-50') + (uploadLocked ? ' opacity-60' : '')}>
            <input ref={inputRef} type="file" accept=".xlsx,.xls,.pdf,.docx" onChange={handleFileSelect} className="hidden" />
            {parsing ? (
              <div className="flex flex-col items-center gap-3"><div className="w-9 h-9 border-[2.5px] border-[var(--navy)] border-t-transparent rounded-full animate-spin" /><p className="text-sm">正在解析文件...</p></div>
            ) : uploadLocked ? (
              <div className="flex flex-col items-center gap-2"><span className="text-3xl">&#10003;</span><p className="text-sm font-medium text-[var(--navy)]">已达到免费体验上限</p><a href="/register" className="px-5 py-2 rounded-lg bg-[var(--navy)] text-white text-xs font-medium hover:bg-[var(--navy-light)]">免费注册</a></div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <svg className="w-10 h-10 text-[var(--navy-light)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-sm font-medium text-[var(--navy)]">拖拽文件到这里，或点击选择</p>
                <p className="text-xs text-[var(--text-secondary)]">支持 .xlsx .xls .pdf .docx · 已解析 {fileEntries.length}/{MAX_FREE_FILES}</p>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {parseError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
            <span className="text-red-500 font-bold text-lg">&#9888;</span>
            <div className="flex-1"><p className="text-sm font-medium text-red-700">解析失败</p><p className="text-xs text-red-500">{parseError}</p></div>
            <button onClick={() => setParseError(null)} className="text-xs text-red-500 underline cursor-pointer">重试</button>
          </div>
        )}

        {/* 3 Feature cards (always visible) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-10">
          {features.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="fc-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <ul>{f.items.map((item, j) => <li key={j}>{item}</li>)}</ul>
            </div>
          ))}
        </div>

        {/* After-upload panels */}
        {fileEntries.length > 0 && (
          <div className="space-y-6">
            {/* File tabs */}
            <div className="flex items-center gap-2 overflow-x-auto thin-scroll">
              {fileEntries.map((entry, idx) => (
                <button key={idx} onClick={() => switchFile(idx)} className={'file-tab ' + (idx === activeFileIdx ? 'active' : '')}>{entry.name}</button>
              ))}
              {!uploadLocked && <button onClick={handleAddFileClick} className="file-tab-add" title="继续上传">+</button>}
              <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.pdf,.docx" onChange={handleAddFileSelect} className="hidden" />
            </div>

            {/* Count + CTA */}
            {activeProducts.length > 0 && (
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-[var(--navy)]">识别到 {activeProducts.length} 个产品{fileEntries[activeFileIdx]?.dedupCount ? '（去重后）' : ''}</p>
                <button onClick={handleGenerateQuotation} disabled={generating}
                  className="px-5 py-2 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 disabled:opacity-50 cursor-pointer">
                  {generating ? '生成中...' : '生成报价单'}
                </button>
              </div>
            )}

            {/* Panel 1 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128269;</div><div className="panel-title">自动解析</div>
                  <p>系统自动提取产品型号、规格和价格，支持多格式文件自动去重整合</p>
                </div>
                <div className="scenario-content flex-1">
                  {activeProducts.length > 0 ? (
                    <div className="max-h-64 overflow-auto thin-scroll">
                      <table className="prod-table">
                        <thead><tr><th>型号</th><th>名称</th><th>规格</th><th>价格</th></tr></thead>
                        <tbody>{activeProducts.slice(0, 50).map((p, i) => (
                          <tr key={i}><td className="font-mono text-[0.75rem]">{p.model || '-'}</td>
                          <td className="max-w-[140px]">{p.name_zh || p.name_en || '-'}</td>
                          <td className="max-w-[160px] text-[var(--text-secondary)]">{p.spec_zh || p.spec_en || '-'}</td>
                          <td className="font-medium">{p.currency === 'USD' ? '$' : '¥'}{p.price_rmb || '-'}</td></tr>
                        ))}</tbody>
                      </table>
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">上传文件后自动显示解析结果</p></div>}
                </div>
              </div>
            </div>

            {/* Panel 2 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128176;</div><div className="panel-title">智能报价</div>
                  <p>自动配图、中英双语、贸易术语计算、汇率实时换算</p>
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
                          <div className="prod-card-body"><div className="name">{p.name_zh || p.name_en || p.model || '产品'}</div>
                          <div className="model">{p.model || ''}</div><div className="qty">数量: {p.quantity || 1}</div></div>
                        </div>
                      ))}
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">上传文件后自动显示产品卡片</p></div>}
                </div>
              </div>
            </div>

            {/* Panel 3 */}
            <div className="scenario-panel panel-fade">
              <div className="flex flex-col md:flex-row">
                <div className="scenario-desc md:w-48 shrink-0">
                  <div className="panel-icon">&#128196;</div><div className="panel-title">全部出单</div>
                  <p>一份数据生成全套外贸单据，带公司信息与专业排版</p>
                </div>
                <div className="scenario-content flex-1">
                  {activeProducts.length > 0 ? (
                    <div className="doc-list">
                      {[
                        ['excel', 'Excel 报价单（含产品图片）', 'check'],
                        ['pdf', 'PDF 报价单', 'check'],
                        ['pi', '形式发票 PI', 'pro'],
                        ['pack', '装箱单', 'pro'],
                        ['pack', '商业发票', 'pro'],
                      ].map(([cls, label, badge], i) => (
                        <div key={i} className="doc-item">
                          <div className={'doc-icon ' + cls}>&#128196;</div>
                          <span className="doc-label">{label}</span>
                          {badge === 'check' ? <span className="doc-check">&#10003;</span> : <span className="doc-badge pro">Pro</span>}
                        </div>
                      ))}
                    </div>
                  ) : <div className="flex items-center justify-center h-40 border-2 border-dashed border-[var(--border)] rounded-xl"><p className="text-sm text-[var(--text-secondary)]">上传文件后显示可生成的单据</p></div>}
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
            <h3 className="text-base font-bold text-[var(--navy)] mb-4">公司信息（可选）</h3>
            <div className="space-y-3">
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">公司名称</label>
              <input value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="输入公司名，不填则用默认" className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">联系人</label>
              <input value={companyContact} onChange={e => setCompanyContact(e.target.value)} placeholder="可选" className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div><label className="text-xs font-medium text-[var(--text-secondary)]">电话</label>
              <input value={companyPhone} onChange={e => setCompanyPhone(e.target.value)} placeholder="可选" className="w-full mt-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg" /></div>
              <div className="border-t pt-3 mt-3">
                <p className="text-xs text-[var(--text-secondary)] mb-2">或上传报价模板自动提取</p>
                <label className="block w-full py-2 text-center rounded-lg border text-sm text-[var(--text-secondary)] hover:bg-gray-50 cursor-pointer">
                  {templateUploading ? '解析中...' : '上传模板 (.xlsx)'}
                  <input type="file" accept=".xlsx,.xls" className="hidden" onChange={e => { if (e.target.files[0]) handleTemplateUpload(e.target.files[0]); }} />
                </label>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCompanyPanel(false)} className="flex-1 py-2 rounded-lg border text-sm cursor-pointer">取消</button>
              <button onClick={confirmQuotation} className="flex-1 py-2 rounded-lg bg-[var(--gold)] text-white text-sm font-medium cursor-pointer">生成报价单</button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
