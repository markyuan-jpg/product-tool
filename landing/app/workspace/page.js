'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { isLoggedIn, getStoredUser, clearAuth, getToken } from '@/lib/auth';
import API_BASE from '@/lib/api';
import { friendlyError } from '@/lib/errors';
import { useLocale, t } from '@/lib/i18n';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export default function WorkspacePage() {
  const { locale, ready } = useLocale();
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [usage, setUsage] = useState(null);
  const [productRefreshKey, setProductRefreshKey] = useState(0);
  const [quotationRefreshKey, setQuotationRefreshKey] = useState(0);

  useEffect(() => {
    const u = getStoredUser();
    if (!u || !isLoggedIn()) { router.push('/login'); return; }
    setUser(u);
    fetch(`${API_BASE}/api/user/usage`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }).then(r => r.json()).then(setUsage).catch(() => {});
  }, [router]);

  const usagePercent = usage ? Math.min(100, Math.round((usage.upload_count / usage.limit) * 100)) : 0;

  if (!ready) return null;

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <Nav />
      {user && user.tier !== 'pro' && usage && (
        <div className="bg-amber-50 border-b border-amber-200">
          <div className="max-w-6xl mx-auto px-4 py-2 flex items-center gap-3 text-xs">
            <span className="text-amber-700 font-medium">{t('workspace.usage.free', locale)}</span>
            <div className="flex-1 max-w-xs h-2 bg-amber-200 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500 rounded-full transition-all" style={{width: usagePercent + '%'}} />
            </div>
            <span className="text-amber-600">
              {t('workspace.usage.uploadCount', locale).replace('{uploadCount}', usage.upload_count).replace('{limit}', usage.limit)} | {t('workspace.usage.productCount', locale).replace('{productCount}', usage.product_count || 0).replace('{productLimit}', usage.product_limit || 200)}
            </span>
            <a href="/pricing" className="ml-auto text-amber-700 font-medium hover:underline">{t('workspace.usage.upgrade', locale)}</a>
          </div>
        </div>
      )}
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        <UploadSection onSaveSuccess={() => setProductRefreshKey(k => k + 1)} />
        <ProductLibrarySection refreshKey={productRefreshKey} user={user} onQuotationGenerated={() => setQuotationRefreshKey(k => k + 1)} />
        <QuotationHistorySection refreshKey={quotationRefreshKey} />
      </main>
      <Footer />
    </div>
  );
}

function UploadSection({ onSaveSuccess }) {
  const { locale } = useLocale();
  const [inputTab, setInputTab] = useState('file');
  const [dragOver, setDragOver] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [products, setProducts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [failedImages, setFailedImages] = useState(new Set());
  const inputRef = useRef(null);
  const [pasteText, setPasteText] = useState('');
  const [pasteImages, setPasteImages] = useState([]);
  const [pasting, setPasting] = useState(false);
  const [pasteError, setPasteError] = useState(null);
  const pasteInputRef = useRef(null);

  const handleFile = async (file) => {
    const valid = ['.xlsx', '.xls', '.pdf', '.docx'].some(e => file.name.toLowerCase().endsWith(e));
    if (!valid) { alert(t('workspace.upload.onlySupport', locale)); return; }
    setParsing(true); setParseError(null);
    try {
      const fd = new FormData(); fd.append('file', file);
      const ac = new AbortController(); const tid = setTimeout(() => ac.abort(), 120000);
      const res = await fetch(API_BASE + '/api/parse', { method: 'POST', body: fd, signal: ac.signal });
      clearTimeout(tid);
      if (!res.ok) { const e = await res.json().catch(() => ({ detail: t('workspace.upload.parseError', locale) })); throw new Error(e.detail || t('workspace.upload.serverError', locale)); }
      const d = await res.json(); setProducts(d.products || []);
      setParsing(false);
    } catch (err) {
      if (err.name === 'AbortError') {
        setParseError(t('workspace.upload.parseTimeout', locale));
      } else {
        setParseError(err.message);
      }
      setParsing(false);
    }
  };

  const handleDrop = useCallback((e) => { e.preventDefault(); e.stopPropagation(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }, []);
  const handleClick = () => inputRef.current?.click();
  const handleFileSelect = (e) => { const f = e.target.files[0]; if (f) handleFile(f); };

  const saveToLib = async () => {
    if (products.length === 0) return;
    setSaving(true); setSaveMsg(null);
    try {
      const b = new URLSearchParams(); b.append('products', JSON.stringify(products));
      const r = await fetch(API_BASE + '/api/products/save', { method: 'POST', headers: { 'Authorization': 'Bearer ' + getToken() }, body: b });
      if (!r.ok) throw new Error(t('workspace.upload.saveFailed', locale));
      setSaveMsg('success'); setProducts([]);
      if (onSaveSuccess) onSaveSuccess();
    } catch (err) { setSaveMsg(err.message); }
    setSaving(false);
  };

  const reset = () => { setParsing(false); setParseError(null); setProducts([]); setSaveMsg(null); setPasteText(''); setPasteImages([]); setPasteError(null); };

  const handlePasteDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation();
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    if (files.length > 0) setPasteImages(prev => [...prev, ...files]);
  }, []);

  const handlePasteImageSelect = (e) => {
    const files = Array.from(e.target.files).filter(f => f.type.startsWith('image/'));
    if (files.length > 0) setPasteImages(prev => [...prev, ...files]);
  };

  const removePasteImage = (idx) => setPasteImages(prev => prev.filter((_, i) => i !== idx));

  const handlePasteParse = async () => {
    if (!pasteText.trim()) return;
    setPasting(true); setPasteError(null);
    try {
      const res = await fetch(API_BASE + '/api/parse-text-products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getToken() },
        body: JSON.stringify({ text: pasteText }),
      });
      if (!res.ok) { const e = await res.json().catch(() => ({ detail: t('workspace.upload.parseError', locale) })); throw new Error(e.detail || t('workspace.upload.serverError', locale)); }
      const d = await res.json();
      setProducts(d.products || []);
      // Match images to products by model number
      if (pasteImages.length > 0 && d.products?.length > 0) {
        const updated = (d.products || []).map(p => {
          const match = pasteImages.find(img => img.name.toLowerCase().includes((p.model || '').toLowerCase()));
          if (match) p._image_path = URL.createObjectURL(match);
          return p;
        });
        setProducts(updated);
      }
      setPasting(false);
    } catch (err) { setPasteError(err.message); setPasting(false); }
  };

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-0 mb-4 border-b border-[var(--border)]">
        <button onClick={() => setInputTab('file')}
          className={'px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ' + (inputTab === 'file' ? 'border-[var(--navy)] text-[var(--navy)]' : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--navy)]')}>
          📁 {t('workspace.upload.title', locale)}
        </button>
        <button onClick={() => setInputTab('smartpaste')}
          className={'px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ' + (inputTab === 'smartpaste' ? 'border-[var(--navy)] text-[var(--navy)]' : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--navy)]')}>
          📋 {t('workspace.upload.pasteTab', locale)}
        </button>
      </div>

      {inputTab === 'file' && (
        <div>
          <div className="drop-zone w-full p-10 sm:p-14 cursor-pointer flex flex-col items-center justify-center gap-3"
            onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
            onDragEnter={() => setDragOver(true)} onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop} onClick={handleClick}>
            <input ref={inputRef} type="file" accept=".xlsx,.xls,.pdf,.docx" className="hidden" onChange={handleFileSelect} />
            {!parsing && !parseError ? (
              <div className="flex flex-col items-center gap-3">
                <svg className="w-10 h-10 text-[var(--navy-light)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-base font-medium">{t('workspace.upload.dragDropBefore', locale)}<span className="text-[var(--navy-light)] underline underline-offset-2">{t('workspace.upload.dragDropLink', locale)}</span></p>
                <p className="text-xs text-[var(--text-secondary)]">{t('workspace.upload.supportedFormats', locale)}</p>
              </div>
            ) : parsing ? (
              <p className="text-sm text-[var(--text-secondary)]">{t('workspace.upload.parsing', locale)}</p>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <p className="text-sm text-[var(--error)]">{parseError}</p>
                <button onClick={(e) => { e.stopPropagation(); reset(); }} className="px-4 py-2 rounded-lg border text-sm cursor-pointer">{t('workspace.upload.reupload', locale)}</button>
              </div>
            )}
          </div>
        </div>
      )}

      {inputTab === 'smartpaste' && (
        <div>
          {/* Image drop zone */}
          <div className="mb-4"
            onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={handlePasteDrop}>
            {pasteImages.length === 0 ? (
              <div onClick={() => pasteInputRef.current?.click()}
                className="border-2 border-dashed border-[var(--border)] rounded-xl p-6 text-center cursor-pointer hover:border-[var(--navy)] hover:bg-gray-50 transition-colors">
                <p className="text-sm text-[var(--text-secondary)]">🖼️ {t('workspace.upload.pasteImageDropBefore', locale)}<span className="text-[var(--navy-light)] underline">{t('workspace.upload.pasteImageDropLink', locale)}</span></p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">{t('workspace.upload.pasteImageHint', locale)}</p>
                <input ref={pasteInputRef} type="file" accept="image/*" multiple className="hidden" onChange={handlePasteImageSelect} />
              </div>
            ) : (
              <div className="border border-[var(--border)] rounded-xl p-4">
                <div className="flex flex-wrap gap-3 mb-2">
                  {pasteImages.map((img, i) => (
                    <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden border border-[var(--border)]">
                      <img src={URL.createObjectURL(img)} alt="" className="w-full h-full object-cover" />
                      <button onClick={() => removePasteImage(i)}
                        className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">×</button>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => pasteInputRef.current?.click()} className="text-xs text-[var(--navy-light)] underline cursor-pointer">{t('workspace.upload.addMoreImages', locale)}</button>
                  <span className="text-xs text-[var(--text-secondary)]">{t('workspace.upload.imageCount', locale).replace('{n}', pasteImages.length)}</span>
                </div>
                <input ref={pasteInputRef} type="file" accept="image/*" multiple className="hidden" onChange={handlePasteImageSelect} />
              </div>
            )}
          </div>

          {/* Text area */}
          <div className="mb-4">
            <textarea value={pasteText} onChange={e => setPasteText(e.target.value)}
              placeholder={t('workspace.upload.pastePlaceholder', locale)}
              className="w-full h-56 p-4 text-sm border border-[var(--border)] rounded-xl resize-y focus:outline-none focus:border-[var(--navy)] placeholder:text-[var(--border)]" />
          </div>

          {/* Parse button */}
          <div className="flex items-center gap-3">
            <button onClick={handlePasteParse} disabled={pasting || !pasteText.trim()}
              className="px-6 py-2.5 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] disabled:opacity-50 cursor-pointer">
              {pasting ? t('workspace.upload.pasting', locale) : t('workspace.upload.pasteBtn', locale)}
            </button>
            {pasteError && <span className="text-sm text-[var(--error)]">{pasteError}</span>}
          </div>
        </div>
      )}
      {products.length > 0 && (
        <div className="mt-6 border border-[var(--border)] rounded-xl bg-[var(--surface)] overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
            <span className="text-sm font-medium text-[var(--navy)]">{t('workspace.upload.result', locale).replace('{count}', products.length)}</span>
          </div>
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-secondary)] text-xs border-b bg-[var(--warm-white)]">
                  <th className="py-2.5 px-4 font-medium">{t('workspace.upload.image', locale)}</th><th className="py-2.5 px-4 font-medium">{t('workspace.upload.model', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.upload.name', locale)}</th><th className="py-2.5 px-4 font-medium">{t('workspace.upload.spec', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.upload.price', locale)}</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p, i) => (
                  <tr key={i} className="border-b border-[var(--border)]/50 hover:bg-[var(--warm-white)]">
                    <td className="py-2 px-4">
                      <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center overflow-hidden">
                        {!failedImages.has(i) && (p._image_path || p.image_path) ? (
                          <img src={API_BASE + '/api/images/?path=' + encodeURIComponent(p._image_path || p.image_path)} alt="" className="w-full h-full object-cover"
                            onError={() => setFailedImages(prev => { const n = new Set(prev); n.add(i); return n; })} />
                        ) : <span className="text-xs text-[var(--text-secondary)]">{t('workspace.upload.noImage', locale)}</span>}
                      </div>
                    </td>
                    <td className="py-2 px-4 font-medium text-[var(--navy)]">{p.model || p.sku || '-'}</td>
                    <td className="py-2 px-4">{p.name_zh || p.name_en || '-'}</td>
                    <td className="py-2 px-4 text-[var(--text-secondary)]">{p.spec_zh || p.spec || '-'}</td>
                    <td className="py-2 px-4">{p.price_raw || ({ 'USD': '$', 'CNY': '¥', 'EUR': '€', 'GBP': '£' }[p.currency] || '$') + (p.price_rmb ?? (p.price ? p.price : '-'))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 border-t border-[var(--border)] flex items-center justify-end gap-3">
            <button onClick={saveToLib} disabled={saving} className="px-5 py-2 rounded-lg bg-[var(--navy)] text-white text-sm font-medium hover:bg-[var(--navy-light)] disabled:opacity-50 cursor-pointer">
              {saving ? t('workspace.upload.saving', locale) : t('workspace.upload.save', locale)}
            </button>
            {saveMsg === 'success' && <span className="text-xs text-[var(--success)]">{t('workspace.upload.saved', locale)}</span>}
            {saveMsg && saveMsg !== 'success' && <span className="text-xs text-[var(--error)]">{saveMsg}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

function ProductLibrarySection({ refreshKey, user, onQuotationGenerated }) {
  const { locale } = useLocale();
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [failedImages, setFailedImages] = useState(new Set());
  const [exportOpen, setExportOpen] = useState(true);
  const [exportType, setExportType] = useState('quotation');
  const [exportLoading, setExportLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState('');
  const [productMeta, setProductMeta] = useState({});
  const [batchQty, setBatchQty] = useState('');

  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [piBuyerName, setPiBuyerName] = useState('');
  const [piBuyerAddress, setPiBuyerAddress] = useState('');
  const [piBuyerContact, setPiBuyerContact] = useState('');
  const [piBuyerTel, setPiBuyerTel] = useState('');
  const [piBuyerEmail, setPiBuyerEmail] = useState('');
  const [piPort, setPiPort] = useState('');
  const [piBrand, setPiBrand] = useState('XXXXX');
  const DEFAULT_PI_PAYMENT = '本合同签订七个工作日内支付定金30%，收到定金后60日内交货，发货前付清剩余70%余款。Terms of payment: The 30% deposit shall be paid within 7 working days after contract signed, with delivery to be completed within 60 days upon receipt of the deposit. The remaining 70% balance must be paid in full prior to shipment.';
  const [piPaymentTerms, setPiPaymentTerms] = useState(DEFAULT_PI_PAYMENT);
  const [piPaymentMethod, setPiPaymentMethod] = useState('T/T');
  const [piCurrency, setPiCurrency] = useState('USD');
  const [tradeTerms, setTradeTerms] = useState('FOB');
  const [tradeLocation, setTradeLocation] = useState('');
  const [quotationLang, setQuotationLang] = useState('chinese');
  const [companyName, setCompanyName] = useState('');
  const [companyContact, setCompanyContact] = useState('');
  const [companyPhone, setCompanyPhone] = useState('');
  const [packingType, setPackingType] = useState('Carton');
  const [packingQty, setPackingQty] = useState('');
  const [shippingPortLoading, setShippingPortLoading] = useState('Qingdao');
  const [shippingPortDischarge, setShippingPortDischarge] = useState('');
  const [shippingVessel, setShippingVessel] = useState('');
  const [shippingBlNo, setShippingBlNo] = useState('');
  const [shippingMarks, setShippingMarks] = useState('N/M');
  const [shippingOrigin, setShippingOrigin] = useState('China');
  const [hsCode, setHsCode] = useState('');
  const [freight, setFreight] = useState('');
  const [insurance, setInsurance] = useState('');
  const [handling, setHandling] = useState('');
  const [deliveryTime, setDeliveryTime] = useState('');
  const [validity, setValidity] = useState('');
  const [exchangeRate, setExchangeRate] = useState('');
  const [includeImages, setIncludeImages] = useState(true);
  // Column selection defaults - all on
  const columnDefs = [
    { key: 'model', label: '型号/名称' },
    { key: 'spec', label: '规格' },
    { key: 'qty', label: '数量' },
    { key: 'price', label: '价格' },
    { key: 'price_cny', label: 'RMB价格' },
    { key: 'photo', label: '图片' },
    { key: 'nw', label: '净重' },
    { key: 'gw', label: '毛重' },
    { key: 'ctn', label: '外箱尺寸' },
    { key: 'cbm', label: '体积' },
    { key: 'upc', label: '每箱数量' },
  ];
  const [selectedColumns, setSelectedColumns] = useState(new Set(columnDefs.map(c => c.key)));

  const toggleColumn = (key) => {
    setSelectedColumns(prev => {
      const n = new Set(prev);
      if (n.has(key)) n.delete(key); else n.add(key);
      return n;
    });
  };
  const [contractNo, setContractNo] = useState('');
  const [poNo, setPoNo] = useState('');
  const [lcNo, setLcNo] = useState('');

  const getMeta = (id, f) => productMeta[id]?.[f] ?? '';
  const setMeta = (id, f, v) => setProductMeta(p => ({ ...p, [id]: { ...p[id], [f]: v } }));
  const getQty = (id) => parseInt(getMeta(id, 'qty')) || 1;
  const setQty = (id, v) => setMeta(id, 'qty', parseInt(v) || 1);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const ac = new AbortController(); const tid = setTimeout(() => ac.abort(), 30000);
      const r = await fetch(API_BASE + '/api/products', { signal: ac.signal, headers: { 'Authorization': 'Bearer ' + getToken() } });
      clearTimeout(tid);
      if (r.status === 401) { clearAuth(); window.location.href = '/login'; return; }
      if (!r.ok) throw new Error(t('workspace.upload.fetchFailed', locale));
      const d = await r.json(); setProducts(d.products || []); setTotal(d.total || 0);
    } catch (err) {
      console.error(err); setProducts([]);
      alert(t('workspace.productLib.loadingFailed', locale) + ': ' + (err.message === 'Failed to fetch' ? t('workspace.upload.connectionFailed', locale) : err.message));
    }
    setLoading(false);
  }, [locale]);

  useEffect(() => { fetchProducts(); }, [fetchProducts, refreshKey]);
  useEffect(() => {
    try {
      const s = JSON.parse(localStorage.getItem('customers') || '[]'); setCustomers(s);
      const es = JSON.parse(localStorage.getItem('export_state') || '{}');
      if (es.tradeTerms) setTradeTerms(es.tradeTerms);
      if (es.piPaymentTerms) setPiPaymentTerms(es.piPaymentTerms);
      if (es.quotationLang) setQuotationLang(es.quotationLang);
      if (es.shippingPortLoading) setShippingPortLoading(es.shippingPortLoading);
      if (es.packingType) setPackingType(es.packingType);
      if (es.freight) setFreight(es.freight);
    } catch (e) {}
  }, []);

  useEffect(() => {
    const s = { tradeTerms, piPaymentTerms, quotationLang, shippingPortLoading, packingType, freight };
    localStorage.setItem('export_state', JSON.stringify(s));
  }, [tradeTerms, piPaymentTerms, quotationLang, shippingPortLoading, packingType, freight]);

  const filtered = products.filter(p => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (p.model || '').toLowerCase().includes(q) || (p.name_zh || '').toLowerCase().includes(q);
  });

  const toggleSelect = (id) => {
    setSelected(prev => { const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  };

  const handleBatchDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(t('workspace.productLib.confirmBatchDelete', locale).replace('{count}', selected.size))) return;
    try {
      const b = new URLSearchParams(); b.append('product_ids', JSON.stringify(Array.from(selected)));
      const r = await fetch(API_BASE + '/api/products/batch-delete', {
        method: 'POST', body: b,
        headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      if (!r.ok) throw new Error(t('workspace.productLib.deleteFailed', locale));
      setSelected(new Set()); fetchProducts();
    } catch (err) { alert(t('workspace.productLib.deleteFailed', locale) + '：' + friendlyError(err)); }
  };

  const handleDelete = async (id) => {
    if (!confirm(t('workspace.productLib.confirmDelete', locale))) return;
    try {
      const r = await fetch(API_BASE + '/api/products/' + id, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + getToken() } });
      if (!r.ok) throw new Error(t('workspace.productLib.deleteFailed', locale));
      fetchProducts();
    } catch (err) { alert(t('workspace.productLib.deleteFailed', locale) + '：' + friendlyError(err)); }
  };

  const saveCustomer = () => {
    if (!piBuyerName) return;
    const c = { name: piBuyerName, address: piBuyerAddress, contact: piBuyerContact, tel: piBuyerTel, email: piBuyerEmail };
    const list = customers.filter(x => x.name !== piBuyerName);
    list.push(c);
    setCustomers(list);
    localStorage.setItem('customers', JSON.stringify(list));
  };

  const loadCustomer = (name) => {
    const c = customers.find(x => x.name === name);
    if (c) { setPiBuyerName(c.name || ''); setPiBuyerAddress(c.address || ''); setPiBuyerContact(c.contact || ''); setPiBuyerTel(c.tel || ''); setPiBuyerEmail(c.email || ''); }
  };

  const deleteCustomer = () => {
    if (!selectedCustomer) return;
    if (!confirm(t('workspace.export.confirmDeleteCustomer', locale).replace('{name}', selectedCustomer))) return;
    const list = customers.filter(x => x.name !== selectedCustomer);
    setCustomers(list);
    localStorage.setItem('customers', JSON.stringify(list));
    setSelectedCustomer('');
    setPiBuyerName('');
    setPiBuyerAddress('');
    setPiBuyerContact('');
    setPiBuyerTel('');
    setPiBuyerEmail('');
  };

  const handleExport = async () => {
    const sel = products.filter(p => selected.has(p.id)).map(p => ({
      ...p,
      qty: getQty(p.id) > 1 ? getQty(p.id) : (parseInt(p.qty) || 1),
      net_weight: parseFloat(getMeta(p.id, 'nw')) || 0, gross_weight: parseFloat(getMeta(p.id, 'gw')) || 0,
      carton_size: getMeta(p.id, 'ctn') || '', cbm: parseFloat(getMeta(p.id, 'cbm')) || 0,
      units_per_carton: parseInt(getMeta(p.id, 'upc')) || 0,
      price_cny: p.price_cny || 0,
      spec_zh: [p.spec_zh, p.price_raw].filter(Boolean).join(' | '),
    }));
    if (sel.length === 0) { alert(t('workspace.export.selectFirst', locale)); return; }
    // 根据 selectedColumns 清空未选列数据
    const colMap = {model:['model','name_zh','name_en'],spec:['spec_zh','spec'],qty:['qty'],price:['price_rmb','price'],price_cny:['price_cny'],photo:['_image_path','image_path'],nw:['net_weight'],gw:['gross_weight'],ctn:['carton_size'],cbm:['cbm'],upc:['units_per_carton']};
    const colEmpty = {model:'',spec:'',qty:1,price:0,price_cny:0,photo:'',nw:0,gw:0,ctn:'',cbm:0,upc:0};
    sel.forEach(item => { Object.entries(colMap).forEach(([key, fields]) => { if (!selectedColumns.has(key)) fields.forEach(f => { item[f] = colEmpty[key]; }); }); });
    setExportLoading(true);
    try {
      const b = new URLSearchParams();
      b.append('products', JSON.stringify(sel));
      b.append('trade_terms', tradeTerms + (tradeLocation ? ' ' + tradeLocation : ''));
      b.append('lang', quotationLang);
      b.append('company_name', companyName);
      b.append('company_contact', companyContact);
      b.append('company_phone', companyPhone);
      b.append('port_loading', shippingPortLoading);
      b.append('port_discharge', shippingPortDischarge);
      b.append('vessel', shippingVessel);
      b.append('bl_no', shippingBlNo);
      b.append('origin_country', shippingOrigin);
      b.append('buyer_name', piBuyerName);
      b.append('buyer_address', piBuyerAddress);
      b.append('buyer_contact', piBuyerContact);
      b.append('buyer_tel', piBuyerTel);
      b.append('buyer_email', piBuyerEmail);
      b.append('packing_type', packingType);
      b.append('packing_qty', packingQty);
      b.append('with_images', includeImages ? '1' : '0');

      if (exportType === 'pi' || exportType === 'invoice') {
        b.append('port_destination', piPort);
        b.append('brand_name', piBrand);
        b.append('payment_terms', piPaymentTerms);
        b.append('currency', piCurrency);
        try {
          const bank = JSON.parse(localStorage.getItem('bank_info') || '{}');
          if (bank.beneficiary) b.append('bank_beneficiary', bank.beneficiary);
          if (bank.bank_name) b.append('bank_name', bank.bank_name);
          if (bank.bank_address) b.append('bank_address', bank.bank_address);
          if (bank.account_no) b.append('bank_account', bank.account_no);
          if (bank.swift_code) b.append('bank_swift', bank.swift_code);
        } catch (e) {}
      }

      if (exportType === 'pi' || exportType === 'quotation') {
        b.append('port_destination', piPort);
        b.append('brand_name', piBrand);
        b.append('payment_terms', piPaymentTerms);
        b.append('currency', piCurrency);
      }

      let url = '', filename = '';
      const ts = Date.now();
      if (exportType === 'quotation') { url = API_BASE + '/api/quotation'; filename = '报价单_' + ts + '.xlsx'; }
      else if (exportType === 'pdf') { url = API_BASE + '/api/quotation/pdf'; filename = '报价单PDF_' + ts + '.pdf'; }
      else if (exportType === 'packing') { url = API_BASE + '/api/packing'; filename = '装箱单_' + ts + '.xlsx'; }
      else if (exportType === 'invoice') { url = API_BASE + '/api/invoice'; filename = '商业发票_' + ts + '.xlsx'; }
      else if (exportType === 'pi') { url = API_BASE + '/api/pi'; filename = '形式发票_' + ts + '.xlsx'; }

      setExportStatus(t('workspace.export.generatingFile', locale).replace('{name}', filename));
      const ac = new AbortController();
      const tid = setTimeout(() => ac.abort(), 120000);
      const r = await fetch(url, {
        method: 'POST', body: b, signal: ac.signal,
        headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      clearTimeout(tid);
      if (!r.ok) throw new Error(t('workspace.upload.generateFailed', locale));
      const ct = r.headers.get('content-type') || '';
      if (ct.includes('json')) {
        const data = await r.json();
        if (data.id) {
          const dlR = await fetch(API_BASE + '/api/quotations/' + data.id + '/download', {
            headers: { 'Authorization': 'Bearer ' + getToken() }
          });
          if (dlR.ok) {
            const blob = await dlR.blob();
            const dlUrl = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = dlUrl; a.download = data.name || filename; a.click();
            setTimeout(() => URL.revokeObjectURL(dlUrl), 5000);
          }
        }
      } else {
        const blob = await r.blob();
        const dlUrl = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = dlUrl; a.download = filename; a.click();
        setTimeout(() => URL.revokeObjectURL(dlUrl), 5000);
      }
      fetchProducts();
      if (onQuotationGenerated) onQuotationGenerated();
    } catch (err) { alert(t('workspace.upload.generateFailed', locale) + '：' + friendlyError(err)); }
    finally { setExportLoading(false); setExportStatus(''); }
  };

  const handleExportAll = async () => {
    const sel = products.filter(p => selected.has(p.id)).map(p => ({
      ...p,
      qty: getQty(p.id) > 1 ? getQty(p.id) : (parseInt(p.qty) || 1),
      net_weight: parseFloat(getMeta(p.id, 'nw')) || 0, gross_weight: parseFloat(getMeta(p.id, 'gw')) || 0,
      carton_size: getMeta(p.id, 'ctn') || '', cbm: parseFloat(getMeta(p.id, 'cbm')) || 0,
      units_per_carton: parseInt(getMeta(p.id, 'upc')) || 0,
      price_cny: p.price_cny || 0,
      spec_zh: [p.spec_zh, p.price_raw].filter(Boolean).join(' | '),
    }));
    if (sel.length === 0) { alert(t('workspace.export.selectFirst', locale)); return; }
    // 根据 selectedColumns 清空未选列数据
    const colMap = {model:['model','name_zh','name_en'],spec:['spec_zh','spec'],qty:['qty'],price:['price_rmb','price'],price_cny:['price_cny'],photo:['_image_path','image_path'],nw:['net_weight'],gw:['gross_weight'],ctn:['carton_size'],cbm:['cbm'],upc:['units_per_carton']};
    const colEmpty = {model:'',spec:'',qty:1,price:0,price_cny:0,photo:'',nw:0,gw:0,ctn:'',cbm:0,upc:0};
    sel.forEach(item => { Object.entries(colMap).forEach(([key, fields]) => { if (!selectedColumns.has(key)) fields.forEach(f => { item[f] = colEmpty[key]; }); }); });
    setExportLoading(true);
    try {
      const ts = Date.now();
      const common = () => {
        const b = new URLSearchParams();
        b.append('products', JSON.stringify(sel));
        b.append('lang', quotationLang);
        b.append('trade_terms', tradeTerms + (tradeLocation ? ' ' + tradeLocation : ''));
        b.append('company_name', companyName);
        b.append('company_contact', companyContact);
        b.append('company_phone', companyPhone);
        b.append('buyer_name', piBuyerName);
        b.append('buyer_address', piBuyerAddress);
        b.append('buyer_contact', piBuyerContact);
        b.append('buyer_tel', piBuyerTel);
        b.append('buyer_email', piBuyerEmail);
        b.append('port_loading', shippingPortLoading);
        b.append('port_discharge', shippingPortDischarge);
        b.append('vessel', shippingVessel);
        b.append('bl_no', shippingBlNo);
        b.append('origin_country', shippingOrigin);
        b.append('packing_type', packingType);
        b.append('packing_qty', packingQty);
        b.append('with_images', includeImages ? '1' : '0');
        return b;
      };
      const tasks = [
        { url: API_BASE + '/api/quotation', name: '报价单_' + ts + '.xlsx',
          build: () => { const b = common(); b.append('payment_terms', piPaymentTerms); b.append('currency', piCurrency); return b; } },
        { url: API_BASE + '/api/quotation/pdf', name: '报价单PDF_' + ts + '.pdf',
          build: () => { const b = common(); b.append('payment_terms', piPaymentTerms); b.append('currency', piCurrency); return b; } },
        { url: API_BASE + '/api/pi', name: '形式发票_' + ts + '.xlsx',
          build: () => { const b = common(); b.append('payment_terms', piPaymentTerms); b.append('currency', piCurrency); b.append('port_destination', piPort); b.append('brand_name', piBrand); return b; } },
        { url: API_BASE + '/api/packing', name: '装箱单_' + ts + '.xlsx',
          build: () => { return common(); } },
        { url: API_BASE + '/api/invoice', name: '商业发票_' + ts + '.xlsx',
          build: () => { const b = common(); b.append('payment_terms', piPaymentTerms); b.append('currency', piCurrency); return b; } },
      ];
      // 串行请求，逐个下载（显示进度）
      const total = tasks.length;
      const downloads = [];
      for (let i = 0; i < total; i++) {
        const task = tasks[i];
        setExportStatus(t('workspace.export.generatingFileProgress', locale).replace('{name}', task.name).replace('{current}', i + 1).replace('{total}', total));
        try {
          const ac = new AbortController();
          const tid2 = setTimeout(() => ac.abort(), 120000);
          const r = await fetch(task.url, {
            method: 'POST', body: task.build(), signal: ac.signal,
            headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/x-www-form-urlencoded' }
          });
          clearTimeout(tid2);
          if (r.ok) {
            const ct = r.headers.get('content-type') || '';
            if (ct.includes('json')) {
              const data = await r.json();
              if (data.id) downloads.push({ id: data.id, name: data.name || task.name });
            } else {
              const blob = await r.blob();
              downloads.push({ blob, name: task.name });
            }
          }
        } catch (e) { /* 单个失败不影响其他 */ }
      }
      setExportStatus(t('workspace.export.downloading', locale));
      // 逐个触发下载
      for (const item of downloads) {
        await new Promise(r => setTimeout(r, 500));
        if (item.id) {
          try {
            const dlR = await fetch(API_BASE + '/api/quotations/' + item.id + '/download', {
              headers: { 'Authorization': 'Bearer ' + getToken() }
            });
            if (dlR.ok) {
              const blob = await dlR.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a'); a.href = url; a.download = item.name; a.click();
              setTimeout(() => URL.revokeObjectURL(url), 5000);
            }
          } catch (e) { /* 单个下载失败不影响其他 */ }
        } else if (item.blob) {
          const url = URL.createObjectURL(item.blob);
          const a = document.createElement('a'); a.href = url; a.download = item.name; a.click();
          setTimeout(() => URL.revokeObjectURL(url), 5000);
        }
      }
      if (onQuotationGenerated) onQuotationGenerated();
    } catch (err) { alert(t('workspace.export.allExportFailed', locale) + '：' + friendlyError(err)); }
    finally { setExportLoading(false); setExportStatus(''); }
  };

  const totalQty = Array.from(selected).reduce((s, id) => s + getQty(id), 0);
  const [liveRate, setLiveRate] = useState(7.2);
  useEffect(() => {
    let ok = true;
    fetch(API_BASE + '/api/exchange-rate?from=USD&to=CNY', { signal: AbortSignal.timeout(5000) })
      .then(r => r.json()).then(d => { if (ok && d.rate) setLiveRate(d.rate); }).catch(() => {});
    return () => { ok = false; };
  }, []);
  const _fmtPrice = (p) => {
    const val = p.price_rmb || 0;
    const prodCur = (p.currency || 'CNY').toUpperCase();
    if (piCurrency === prodCur) return val;
    // 币种不同，需要换算
    if (piCurrency === 'USD' && prodCur === 'CNY') return val / liveRate;
    if (piCurrency === 'CNY' && prodCur === 'USD') return val * liveRate;
    return val;
  };
  const _curSym = { 'USD': '$', 'CNY': '¥', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'KRW': '₩' };
  const sym = _curSym[piCurrency] || '$';
  const totalAmt = products.filter(p => selected.has(p.id)).reduce((s, p) => s + _fmtPrice(p) * getQty(p.id), 0);
  const tNW = Array.from(selected).reduce((s, id) => s + (parseFloat(getMeta(id, 'nw')) || 0) * getQty(id), 0);
  const tGW = Array.from(selected).reduce((s, id) => s + (parseFloat(getMeta(id, 'gw')) || 0) * getQty(id), 0);

  const [openSections, setOpenSections] = useState(new Set(['company']));

  const toggleSection = (key) => {
    setOpenSections(prev => {
      const n = new Set(prev);
      if (n.has(key)) n.delete(key); else n.add(key);
      return n;
    });
  };

  const ExportSection = ({ title, icon, sectionKey, children }) => {
    const isOpen = openSections.has(sectionKey);
    return (
      <div className="border border-[var(--border)] rounded-lg overflow-hidden">
        <button onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between px-3 py-2 bg-[var(--warm-white)] hover:bg-gray-100/50 text-left cursor-pointer">
          <span className="text-sm font-semibold text-[var(--navy)]">{icon} {title}</span>
          <svg className={'w-3.5 h-3.5 text-[var(--text-secondary)] transition-transform ' + (isOpen ? 'rotate-180' : '')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && <div className="p-3 space-y-2 bg-white">{children}</div>}
      </div>
    );
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-[var(--navy)]">{t('workspace.productLib.title', locale)}</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[var(--text-secondary)]">{t('workspace.productLib.total', locale).replace('{count}', total)}</span>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder={t('workspace.productLib.search', locale)} className="px-3 py-1.5 text-sm border border-[var(--border)] rounded-lg w-44" />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-3 border-[var(--gold)] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : products.length === 0 ? (
        <div className="border border-[var(--border)] rounded-xl bg-[var(--surface)] p-12 text-center">
          <p className="text-sm text-[var(--text-secondary)]">{t('workspace.productLib.empty', locale)}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">{t('workspace.productLib.emptyHint', locale)}</p>
        </div>
      ) : (
        <div className="border border-[var(--border)] rounded-xl bg-[var(--surface)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-secondary)] text-xs border-b bg-[var(--warm-white)]">
                  <th className="py-2.5 px-4 w-10">
                    <input type="checkbox" className="accent-[var(--navy)]"
                      checked={filtered.length > 0 && filtered.every(p => selected.has(p.id))}
                      onChange={() => setSelected(prev => {
                        const allSel = filtered.every(p => prev.has(p.id));
                        const n = new Set(prev);
                        filtered.forEach(p => { if (allSel) n.delete(p.id); else n.add(p.id); });
                        return n;
                      })} />
                  </th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.productLib.products', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.productLib.image', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.productLib.spec', locale)}</th>
                  <th className="py-2.5 px-4 font-medium w-16">{t('workspace.productLib.qty', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.productLib.price', locale)}</th>
                  <th className="py-2.5 px-4 font-medium">{t('workspace.productLib.action', locale)}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.id} className={'border-b border-[var(--border)]/50 hover:bg-[var(--warm-white)]' + (selected.has(p.id) ? ' bg-[var(--warm-white)]' : '')}>
                    <td className="py-2.5 px-4"><input type="checkbox" className="accent-[var(--navy)]" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} /></td>
                    <td className="py-2.5 px-4">
                      <div className="font-medium text-[var(--navy)]">{p.model || p.sku || '-'}</div>
                      <div className="text-xs text-[var(--text-secondary)]">{p.name_zh || p.name_en || ''}</div>
                    </td>
                    <td className="py-2.5 px-4">
                      <div className="w-[60px] h-[60px] flex items-center justify-center">
                        {p.image_path ? (
                          <img src={API_BASE + '/api/images/?path=' + encodeURIComponent(p.image_path)}
                            className="w-[60px] h-[60px] object-cover rounded border" loading="lazy"
                            onError={(e) => { e.currentTarget.style.display = 'none'; const el = e.currentTarget.nextElementSibling; if (el) el.style.display = 'flex'; }} alt="" />
                        ) : null}
                        <div className={'w-[60px] h-[60px] bg-gray-50 rounded border border-dashed items-center justify-center text-xs text-gray-300 ' + (p.image_path ? 'hidden' : 'flex')}>{t('workspace.upload.noImage', locale)}</div>
                      </div>
                    </td>
                    <td className="py-2.5 px-4 text-[var(--text-secondary)] max-w-[200px]" title={p.spec_zh || p.spec || ''}>
                      {(() => {
                        const raw = (p.spec_zh || p.spec || '').trim();
                        if (!raw) return <span className="text-xs text-gray-300">{t('workspace.productLib.noSpec', locale)}</span>;
                        const parts = raw.split(/[;\n]/).map(s => s.trim()).filter(Boolean);
                        const preview = parts.slice(0, 2);
                        const more = parts.length > 2 ? parts.length - 2 : 0;
                        return preview.map((part, idx) => (
                          <span key={idx} className="block text-xs leading-5">{part}</span>
                        )).concat(more > 0 ? <span key="more" className="text-[10px] text-gray-400">{t('workspace.productLib.specMore', locale).replace('{n}', more)}</span> : null);
                      })()}
                    </td>
                    <td className="py-2.5 px-4">
                      <input type="number" min="1" value={getQty(p.id)}
                        onChange={e => setQty(p.id, e.target.value)}
                        className="w-14 px-2 py-1 text-sm border border-[var(--border)] rounded text-center" />
                    </td>
                    <td className="py-2.5 px-4">{sym}{(p.currency === 'USD' ? p.price_rmb || 0 : _fmtPrice(p)).toFixed(2)}</td>
                    <td className="py-2.5 px-4">
                      <button onClick={() => handleDelete(p.id)} className="text-xs text-[var(--error)] hover:underline cursor-pointer">{t('workspace.productLib.delete', locale)}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="px-5 py-3 border-t border-[var(--border)] flex items-center justify-between">
            <span className="text-sm text-[var(--text-secondary)]">{selected.size > 0 ? t('workspace.productLib.selected', locale).replace('{count}', selected.size) : t('workspace.productLib.noSelection', locale)}</span>
            <div className="flex items-center gap-2">
              <button onClick={() => setSelected(prev => {
                if (filtered.every(p => prev.has(p.id))) return new Set();
                else return new Set(filtered.map(p => p.id));
              })} className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm hover:bg-gray-50 cursor-pointer">{t('workspace.productLib.selectAll', locale)}</button>
              {selected.size > 0 && (
                <button onClick={handleBatchDelete} className="px-3 py-1.5 rounded-lg text-sm font-medium text-white bg-[var(--error)] hover:bg-red-700 cursor-pointer">{t('workspace.productLib.batchDelete', locale).replace('{count}', selected.size)}</button>
              )}
            </div>
          </div>

          {/* Export Panel */}
          {selected.size > 0 && (
            <div className="border-t border-[var(--border)] bg-[var(--warm-white)]">
              <button onClick={() => setExportOpen(!exportOpen)}
                className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-100/50 cursor-pointer">
                <span className="text-sm font-semibold text-[var(--navy)]">📄 {t('workspace.productLib.exportSettings', locale)}</span>
                <svg className={'w-4 h-4 text-[var(--text-secondary)] transition-transform ' + (exportOpen ? 'rotate-180' : '')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {exportOpen && (
                <div className="px-5 pb-5 space-y-3">
                  {exportOpen && (exportType === 'quotation' || exportType === 'pdf' || user?.tier === 'pro') && (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {/* Company Info */}
                      <ExportSection title={t('workspace.export.company', locale)} icon="🏢" sectionKey="company">
                        <div className="text-xs"><span className="text-[var(--text-secondary)]">{t('workspace.export.shipper', locale)}</span> <span className="font-medium">{companyName || 'XXXXX'}</span></div>
                        <div className="flex gap-2">
                          <input type="text" value={piBuyerName} onChange={e => setPiBuyerName(e.target.value)} placeholder={t('workspace.export.phBuyerName', locale)} className="flex-1 px-3 py-1.5 text-sm border rounded-lg" />
                          <button onClick={saveCustomer} className="px-3 py-1.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-xs hover:bg-[var(--navy)] hover:text-white cursor-pointer">{t('workspace.export.saveCustomer', locale)}</button>
                          <select value={selectedCustomer} onChange={e => { setSelectedCustomer(e.target.value); loadCustomer(e.target.value); }}
                            className="w-32 px-2 py-1.5 text-sm border rounded-lg bg-white">
                            <option value="">{t('workspace.export.existingCustomer', locale)}</option>
                            {customers.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                          </select>
                          {selectedCustomer && (
                            <button onClick={deleteCustomer} className="px-2 py-1.5 rounded-lg border border-red-300 text-red-500 text-xs hover:bg-red-50 cursor-pointer" title={t('workspace.export.deleteCustomer', locale)}>🗑</button>
                          )}
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <input type="text" value={piBuyerAddress} onChange={e => setPiBuyerAddress(e.target.value)} placeholder={t('workspace.export.phAddress', locale)} className="px-3 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={piBuyerContact} onChange={e => setPiBuyerContact(e.target.value)} placeholder={t('workspace.export.phContact', locale)} className="px-3 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={piBuyerTel} onChange={e => setPiBuyerTel(e.target.value)} placeholder={t('workspace.export.phTel', locale)} className="px-3 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={piBuyerEmail} onChange={e => setPiBuyerEmail(e.target.value)} placeholder={t('workspace.export.phEmail', locale)} className="px-3 py-1.5 text-sm border rounded-lg" />
                        </div>
                      </ExportSection>

                      {/* Products Detail */}
                      <ExportSection title={t('workspace.export.products', locale)} icon="📦" sectionKey="products">
                        <div className="overflow-x-auto bg-white rounded-lg border p-2">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="text-left text-[var(--text-secondary)] border-b">
                                <th className="py-1 px-1">{t('workspace.export.model', locale)}</th><th className="py-1 px-1 w-14">{t('workspace.export.qty', locale)}</th>
                                <th className="py-1 px-1 w-12">{t('workspace.export.nw', locale)}</th><th className="py-1 px-1 w-12">{t('workspace.export.gw', locale)}</th>
                                <th className="py-1 px-1 w-20">{t('workspace.export.size', locale)}</th><th className="py-1 px-1 w-12">{t('workspace.export.cbm', locale)}</th><th className="py-1 px-1 w-12">{t('workspace.export.perCarton', locale)}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {products.filter(p => selected.has(p.id)).map(p => (
                                <tr key={p.id} className="border-b border-[var(--border)]/50">
                                  <td className="py-1 px-1 font-medium text-[var(--navy)] text-[11px]">{p.model}</td>
                                  <td className="py-1 px-1"><input type="number" min="1" value={getQty(p.id)} onChange={e => setQty(p.id, e.target.value)} className="w-11 px-1 py-0.5 text-xs border rounded text-center" /></td>
                                  {[['nw', 'net_weight', '净重', '8'], ['gw', 'gross_weight', '毛重', '8'], ['ctn', 'carton_size', '尺寸', '12'], ['cbm', 'cbm', 'CBM', '8'], ['upc', 'units_per_carton', '每箱', '8']].map(([k, dbk, lb, w]) =>
                                    <td key={k} className="py-1 px-1">
                                      <input type="text" value={getMeta(p.id, k) !== undefined ? getMeta(p.id, k) : (p[dbk] || '')}
                                        onChange={e => setMeta(p.id, k, e.target.value)} className={'w-' + w + ' px-1 py-0.5 text-xs border rounded text-center'} />
                                    </td>
                                  )}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <div className="flex items-center gap-3 mt-2 text-xs">
                            <span className="text-[var(--text-secondary)]">{t('workspace.export.batchQty', locale)}</span>
                            <span>{t('workspace.export.qty', locale)} <input type="number" min="1" value={batchQty} onChange={e => setBatchQty(e.target.value)} className="w-12 ml-1 px-1 py-0.5 border rounded text-center" /></span>
                            <button onClick={() => { const v = parseInt(batchQty) || 1; setProductMeta(p => { const n = { ...p }; products.filter(x => selected.has(x.id)).forEach(x => { n[x.id] = { ...n[x.id], qty: v }; }); return n; }); }}
                              className="px-1.5 py-0.5 rounded bg-[var(--navy)]/10 text-[var(--navy)] hover:bg-[var(--navy)]/20 cursor-pointer">↕ {t('workspace.export.batchApply', locale)}</button>
                          </div>
                        </div>
                      </ExportSection>

                      {/* Shipping */}
                      <ExportSection title={t('workspace.export.shipping', locale)} icon="🚢" sectionKey="shipping">
                        <div className="flex gap-1">
                          <select value={tradeTerms} onChange={e => setTradeTerms(e.target.value)} className="w-20 px-1 py-1.5 text-sm border rounded-lg bg-white">
                            <option>EXW</option><option>FOB</option><option>CIF</option><option>DDP</option>
                          </select>
                          <input type="text" value={tradeLocation} onChange={e => setTradeLocation(e.target.value)} placeholder={t('workspace.export.phLocation', locale)} className="flex-1 px-2 py-1.5 text-sm border rounded-lg" />
                        </div>
                        {tradeTerms !== 'EXW' && (
                          <div className="grid grid-cols-2 gap-2">
                            <input type="text" value={shippingPortLoading} onChange={e => setShippingPortLoading(e.target.value)} placeholder={t('workspace.export.phPortLoading', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                            <input type="text" value={shippingPortDischarge} onChange={e => setShippingPortDischarge(e.target.value)} placeholder={t('workspace.export.phPortDischarge', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                            <input type="text" value={shippingVessel} onChange={e => setShippingVessel(e.target.value)} placeholder={t('workspace.export.phVessel', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                            <input type="text" value={shippingBlNo} onChange={e => setShippingBlNo(e.target.value)} placeholder={t('workspace.export.phBlNo', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                            <input type="text" value={shippingMarks} onChange={e => setShippingMarks(e.target.value)} placeholder={t('workspace.export.phMarks', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                            <input type="text" value={shippingOrigin} onChange={e => setShippingOrigin(e.target.value)} placeholder={t('workspace.export.phOrigin', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          </div>
                        )}
                        <div className="flex gap-2">
                          <select value={packingType} onChange={e => setPackingType(e.target.value)} className="px-2 py-1.5 text-sm border rounded-lg bg-white">
                            <option>Carton</option><option>Pallet</option><option>Box</option><option>Bag</option><option>Drum</option>
                          </select>
                          <input type="text" value={packingQty} onChange={e => setPackingQty(e.target.value)} placeholder={t('workspace.export.phPackingQty', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                        </div>
                        <div className="flex gap-4 text-xs">
                          <span>{t('workspace.export.deliveryTime', locale)} <input type="text" value={deliveryTime} onChange={e => setDeliveryTime(e.target.value)} placeholder={t('workspace.export.deliveryPlaceholder', locale)} className="ml-1 px-2 py-0.5 border rounded w-28" /></span>
                          <span>{t('workspace.export.validity', locale)} <input type="text" value={validity} onChange={e => setValidity(e.target.value)} placeholder={t('workspace.export.validityPlaceholder', locale)} className="ml-1 px-2 py-0.5 border rounded w-28" /></span>
                        </div>
                      </ExportSection>

                      {/* Payment */}
                      <ExportSection title={t('workspace.export.payment', locale)} icon="💰" sectionKey="payment">
                        <div className="flex gap-2">
                          <select value={piPaymentMethod} onChange={e => setPiPaymentMethod(e.target.value)} className="w-16 px-1 py-1.5 text-sm border rounded-lg bg-white">
                            <option>T/T</option><option>L/C</option><option>D/P</option><option>D/A</option>
                          </select>
                          <textarea rows={2} value={piPaymentTerms} onChange={e => setPiPaymentTerms(e.target.value)} placeholder={t('workspace.export.phPaymentTerms', locale)} className="w-full px-2 py-1.5 text-sm border rounded-lg" />
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <input type="text" value={contractNo} onChange={e => setContractNo(e.target.value)} placeholder={t('workspace.export.phContractNo', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={poNo} onChange={e => setPoNo(e.target.value)} placeholder={t('workspace.export.phPoNo', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={lcNo} onChange={e => setLcNo(e.target.value)} placeholder={t('workspace.export.phLcNo', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                        </div>
                        <input type="text" value={piPort} onChange={e => setPiPort(e.target.value)} placeholder={t('workspace.export.phDestinationPort', locale)} className="w-full px-2 py-1.5 text-sm border rounded-lg" />
                        <input type="text" value={piBrand} onChange={e => setPiBrand(e.target.value)} placeholder={t('workspace.export.phBrand', locale)} className="w-full px-2 py-1.5 text-sm border rounded-lg" />
                        <div className="flex gap-4 text-xs">
                          <span>{t('workspace.export.exchangeRate', locale)} <input type="text" value={exchangeRate} onChange={e => setExchangeRate(e.target.value)} placeholder={t('workspace.export.realTime', locale)} className="ml-1 px-2 py-0.5 border rounded w-20" />{t('workspace.export.realTimeHint', locale)}</span>
                        </div>
                      </ExportSection>

                      </div>
                      {/* Notes */}
                      <ExportSection title={t('workspace.export.notes', locale)} icon="📝" sectionKey="notes">
                        <div className="grid grid-cols-4 gap-2">
                          <input type="text" value={freight} onChange={e => setFreight(e.target.value)} placeholder={t('workspace.export.phFreight', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={insurance} onChange={e => setInsurance(e.target.value)} placeholder={t('workspace.export.phInsurance', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={handling} onChange={e => setHandling(e.target.value)} placeholder={t('workspace.export.phHandling', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                          <input type="text" value={hsCode} onChange={e => setHsCode(e.target.value)} placeholder={t('workspace.export.phHsCode', locale)} className="px-2 py-1.5 text-sm border rounded-lg" />
                        </div>
                      </ExportSection>

                      {/* Columns Selection */}
                      <ExportSection title={t('workspace.export.columns', locale)} icon="☑️" sectionKey="columns">
                        <div className="flex flex-wrap gap-2">
                          {columnDefs.map(c => (
                            <label key={c.key} className="flex items-center gap-1.5 px-2 py-1 rounded border border-[var(--border)] text-xs cursor-pointer hover:bg-gray-50"
                              onClick={() => toggleColumn(c.key)}>
                              <input type="checkbox" checked={selectedColumns.has(c.key)} onChange={() => {}} className="accent-[var(--navy)]" />
                              {t('workspace.export.col' + c.key, locale)}
                            </label>
                          ))}
                          <label className="flex items-center gap-1.5 px-2 py-1 rounded border border-[var(--gold)] text-xs cursor-pointer hover:bg-yellow-50"
                            onClick={() => setIncludeImages(v => !v)}>
                            <input type="checkbox" checked={includeImages} onChange={() => {}} className="accent-[var(--gold)]" />
                            🖼 {t('workspace.export.includeImages', locale)}
                          </label>
                        </div>
                      </ExportSection>

                      {/* Export type + Language + Currency */}
                      <div className="border border-[var(--border)] rounded-lg p-3 bg-white space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs text-[var(--text-secondary)] font-medium">{t('workspace.export.exportType', locale)}</span>
                          {(user?.tier === 'pro' ? ['quotation', 'pdf', 'pi', 'packing', 'invoice'] : ['quotation', 'pdf']).map(docType => (
                            <button key={docType} onClick={() => setExportType(docType)}
                              className={'px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer ' +
                                (exportType === docType ? 'bg-[var(--navy)] text-white' : 'bg-white border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--navy)]')}>
                              {docType === 'quotation' ? t('workspace.export.excelQuote', locale) : docType === 'pdf' ? t('workspace.export.pdfQuote', locale) : docType === 'pi' ? t('workspace.export.pi', locale) : docType === 'packing' ? t('workspace.export.packingList', locale) : t('workspace.export.invoice', locale)}
                            </button>
                          ))}
                          {user?.tier !== 'pro' && <span className="text-[10px] text-amber-600 ml-1">{t('workspace.export.proNote', locale)}</span>}
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-[var(--text-secondary)]">{t('workspace.export.lang', locale)}</span>
                            <select value={quotationLang} onChange={e => setQuotationLang(e.target.value)}
                              className="px-2 py-1.5 text-xs border border-[var(--border)] rounded-lg bg-white">
                              <option value="chinese">{t('workspace.export.chinese', locale)}</option>
                              <option value="english">{t('workspace.export.english', locale)}</option>
                              <option value="bilingual">{t('workspace.export.bilingual', locale)}</option>
                            </select>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-[var(--text-secondary)]">{t('workspace.export.currency', locale)}</span>
                            <select value={piCurrency} onChange={e => setPiCurrency(e.target.value)}
                              className="px-2 py-1.5 text-xs border border-[var(--border)] rounded-lg bg-white">
                              <option value="USD">USD</option>
                              <option value="CNY">CNY</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Preview with language support */}
                      <div className="border border-[var(--border)] rounded-lg p-3 bg-white">
                        <p className="text-xs text-[var(--text-secondary)] mb-2">📋 {t('workspace.export.preview', locale)}</p>
                        <div className="text-[11px] leading-relaxed text-[var(--text-primary)] bg-[var(--warm-white)] p-3 rounded border">
                          {(() => {
                            const L = quotationLang;
                            const isCh = L === 'chinese' || L === 'bilingual';
                            const isEn = L === 'english' || L === 'bilingual';
                            const _t = (zh, en) => isCh && isEn ? zh + ' / ' + en : isCh ? zh : en;
                            const qTitle = _t('外贸报价单', 'FOREIGN TRADE QUOTATION');
                            const piTitle = _t('形式发票', 'PROFORMA INVOICE');
                            const plTitle = _t('装箱单', 'PACKING LIST');
                            const ciTitle = _t('商业发票', 'COMMERCIAL INVOICE');
                            const pdfTitle = _t('PDF报价单', 'PDF QUOTATION');
                            const supplier = _t('供应商', 'Supplier');
                            const items = _t('产品', 'Items');
                            const totalLabel = _t('合计', 'Total');
                            const payTerms = _t('付款条件', 'Payment Terms');
                            const toLabel = _t('致', 'To');
                            const dateLabel = _t('日期', 'Date');
                            const shippingLabel = _t('运输信息', 'Shipping');
                            return (
                              <>
                                 {exportType === 'quotation' && (
                                  <div>
                                    <p className="font-bold text-center text-sm">{qTitle}</p>
                                    <p className="mt-1">{supplier}: {companyName || 'XXXXX'} | {dateLabel}: {new Date().toLocaleDateString(L === 'chinese' ? 'zh-CN' : 'en-US')}</p>
                                    <p>Trade Terms: {tradeTerms} {tradeLocation || 'XXXXX'} | Currency: {piCurrency}</p>
                                    <p className="mt-1">{items}:</p>
                                    {products.filter(p => selected.has(p.id)).slice(0, 3).map((p, i) => (
                                      <p key={p.id} className="text-[10px]">  {i + 1}. {p.model} x{getQty(p.id)} - {sym}{_fmtPrice(p).toFixed(2)}</p>
                                    ))}
                                    {selected.size > 3 && <p className="text-[10px]">  ... {_t('共', 'total')} {selected.size} {_t('项', 'items')}</p>}
                                    <p className="mt-1 font-bold">{totalLabel}: {sym}{totalAmt.toFixed(2)}</p>
                                    <p className="text-[9px] text-gray-400 mt-1">{payTerms}: {piPaymentTerms.slice(0,80)}{piPaymentTerms.length > 80 ? '...' : ''}</p>
                                    <p className="text-[9px] text-gray-400">{shippingLabel}: {tradeTerms} {tradeLocation} | {shippingPortLoading} → {shippingPortDischarge || 'XXX'}</p>
                                  </div>
                                )}
                                 {exportType === 'pi' && (
                                  <div>
                                    <p className="font-bold text-center text-sm">{piTitle}</p>
                                    <p>{toLabel}: {piBuyerName || 'XXXXX'}{piBuyerAddress ? ', ' + piBuyerAddress : ''}</p>
                                    <p>{_t('币种','Currency')}: {piCurrency} | {_t('贸易条款','Terms')}: {tradeTerms} {tradeLocation || 'XXXXX'} | {_t('目的港','Port')}: {piPort || '___'}</p>
                                    <p className="mt-1">{items}:</p>
                                    {products.filter(p => selected.has(p.id)).slice(0, 3).map((p, i) => (
                                      <p key={p.id} className="text-[10px]">  {i + 1}. {p.model} x{getQty(p.id)} - {sym}{_fmtPrice(p).toFixed(2)}</p>
                                    ))}
                                    <p className="mt-1 font-bold">{totalLabel}: {sym}{totalAmt.toFixed(2)}</p>
                                    <div className="mt-1 border-t border-gray-200 pt-1">
                                      <p className="text-[9px] text-gray-500 font-semibold">{_t('条款','Terms & Conditions')}:</p>
                                      <p className="text-[8px] text-gray-500">1. {payTerms}: {piPaymentTerms.slice(0, 60)}{piPaymentTerms.length > 60 ? '...' : ''}</p>
                                      <p className="text-[8px] text-gray-500">2. {_t('交货期','Delivery')}: {_t('收到付款后60天内','60 days upon receipt of payment.')}</p>
                                      <p className="text-[8px] text-gray-500">3. {_t('目的港','Port of destination')}: {piPort || '___'}</p>
                                      <p className="text-[8px] text-gray-500">4. {_t('品牌','Brand')}: {piBrand || 'XXXXX'}</p>
                                      <p className="text-[8px] text-gray-500">5. {_t('有效期','Validity')}: {_t('报价30天内有效','Valid for 30 days')}</p>
                                      <p className="text-[8px] text-gray-500">6. {_t('保险由买方负责','Insurance: To be covered by the buyer.')}</p>
                                    </div>
                                  </div>
                                )}
                                {exportType === 'packing' && (
                                  <div>
                                    <p className="font-bold text-center text-sm">{plTitle}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('1. 发货人','1. Shipper (Exporter):')}</span> {companyName || 'XXXXX'}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('2. 收货人','2. Consignee (Buyer):')}</span> {piBuyerName || 'XXXXX'}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('3. 运输信息','3. Transport Details:')}</span> {shippingPortLoading} → {shippingPortDischarge || 'XXX'} {shippingVessel ? 'Vessel: ' + shippingVessel : ''}</p>
                                    <p className="mt-1 text-[9px] font-semibold">{_t('装箱明细','Packing List')}:</p>
                                    <div className="text-[8px] mt-0.5">
                                      <div className="grid grid-cols-5 gap-1 font-semibold border-b pb-0.5 mb-0.5">
                                        <span>{_t('型号','Model')}</span><span>{_t('数量','Qty')}</span><span>{_t('净重','NW')}</span><span>{_t('毛重','GW')}</span><span>{_t('体积','CBM')}</span>
                                      </div>
                                      {products.filter(p => selected.has(p.id)).slice(0, 3).map((p, i) => (
                                        <div key={p.id} className="grid grid-cols-5 gap-1">
                                          <span>{p.model}</span><span>{getQty(p.id)}</span><span>{parseFloat(getMeta(p.id, 'nw') || p.net_weight || 0).toFixed(1)}</span><span>{parseFloat(getMeta(p.id, 'gw') || p.gross_weight || 0).toFixed(1)}</span><span>{parseFloat(getMeta(p.id, 'cbm') || p.cbm || 0).toFixed(3)}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <p className="text-[9px] mt-1">{_t('合计','TOTAL')}: {totalQty} {_t('件','units')} | NW: {tNW.toFixed(1)}kg | GW: {tGW.toFixed(1)}kg</p>
                                  </div>
                                )}
                                {exportType === 'invoice' && (
                                  <div>
                                    <p className="font-bold text-center text-sm">{ciTitle}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('1. 卖方','1. Seller:')}</span> {companyName || 'XXXXX'}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('2. 买方','2. Buyer:')}</span> {piBuyerName || 'XXXXX'}{piBuyerAddress ? ', ' + piBuyerAddress : ''}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('3. 运输','3. Transport:')}</span> {_t('启运港','Port of Loading')}: {shippingPortLoading} | {_t('目的港','Port of Discharge')}: {shippingPortDischarge || 'XXXXX'} | {_t('船名','Vessel')}: {shippingVessel || '___'}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('4. 唛头','4. Marks & No.:')}</span> {shippingMarks || 'N/M'}</p>
                                    <p className="mt-1 text-[9px] font-semibold">{_t('货物明细','Description of Goods')}:</p>
                                    <div className="text-[8px] mt-0.5">
                                      <div className="grid grid-cols-6 gap-1 font-semibold border-b pb-0.5 mb-0.5">
                                        <span>#</span><span className="col-span-2">{_t('型号/名称','Description')}</span><span>{_t('数量','Qty')}</span><span>{_t('单价','Unit Price')}</span><span>{_t('金额','Total')}</span>
                                      </div>
                                      {products.filter(p => selected.has(p.id)).slice(0, 4).map((p, i) => (
                                        <div key={p.id} className="grid grid-cols-6 gap-1">
                                          <span>{i+1}</span><span className="col-span-2">{p.model}</span><span>{getQty(p.id)}</span><span>{sym}{_fmtPrice(p).toFixed(2)}</span><span>{sym}{_fmtPrice(p) * getQty(p.id)}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <p className="text-[9px] mt-1">{_t('小计','Subtotal')}: {sym}{totalAmt.toFixed(2)} | {_t('总数量','Total Qty')}: {totalQty}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('付款条件','Payment Terms')}:</span> {piPaymentTerms.slice(0, 60)}</p>
                                    <p className="text-[9px]"><span className="font-semibold">{_t('贸易条款','Incoterms')}:</span> {tradeTerms} {tradeLocation || ''}</p>
                                  </div>
                                )}
                                {exportType === 'pdf' && (
                                  <div>
                                    <p className="font-bold text-center text-sm">{pdfTitle}</p>
                                    <p>{_t('和Excel报价单相同格式导出为PDF','Same format as Excel quotation, exported as PDF.')}</p>
                                    <p>{items}: {selected.size} {_t('项','items')} | {totalLabel}: {sym}{totalAmt.toFixed(2)}</p>
                                  </div>
                                )}
                              </>
                            );
                          })()}
                        </div>
                      </div>

                      {/* Export button section */}
                      <div className="flex items-center justify-end gap-3">
                        {exportStatus && <span className="text-xs text-[var(--text-secondary)]">{exportStatus}</span>}
                        {user?.tier === 'pro' && (
                        <button onClick={handleExportAll} disabled={exportLoading}
                          className="px-6 py-2.5 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 disabled:opacity-50 cursor-pointer">
                          {exportLoading ? t('workspace.export.generating', locale) : '⚡ ' + t('workspace.export.allExport', locale)}
                        </button>
                        )}
                        <button onClick={handleExport} disabled={exportLoading}
                          className="px-4 py-2.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-sm font-medium hover:bg-[var(--navy)] hover:text-white disabled:opacity-50 cursor-pointer">
                          {exportLoading ? t('workspace.export.generating', locale) : '📥 ' + t('workspace.export.generateAndDownload', locale)}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function QuotationHistorySection({ refreshKey }) {
  const { locale } = useLocale();
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState(new Set());

  const fetchQuotations = useCallback(async () => {
    setLoading(true);
    try {
      const ac = new AbortController(); const tid = setTimeout(() => ac.abort(), 30000);
      const r = await fetch(API_BASE + '/api/quotations', { signal: ac.signal, headers: { 'Authorization': 'Bearer ' + getToken() } });
      clearTimeout(tid);
      if (!r.ok) throw new Error(t('workspace.quotationHistory.downloadFailed', locale));
      const d = await r.json(); setQuotations(d.quotations || []);
    } catch (err) { console.error(err); setQuotations([]); }
    setLoading(false);
  }, [locale]);

  useEffect(() => { fetchQuotations(); }, [fetchQuotations, refreshKey]);

  const toggleSelect = (id) => {
    setSelectedIds(prev => { const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  };

  const handleSelectAll = () => {
    if (quotations.every(q => selectedIds.has(q.id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(quotations.map(q => q.id)));
    }
  };

  const handleDownload = async (id) => {
    try {
      const r = await fetch(API_BASE + '/api/quotations/' + id + '/download', { headers: { 'Authorization': 'Bearer ' + getToken() } });
      if (r.status === 401) { clearAuth(); window.location.href = '/login'; return; }
      if (!r.ok) throw new Error(t('workspace.quotationHistory.downloadFailed', locale));
      const blob = await r.blob();
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
      const cd = r.headers.get('content-disposition');
      a.download = cd ? cd.split('filename=')[1]?.replace(/"/g, '') || 'quotation.xlsx' : 'quotation.xlsx';
      a.click(); URL.revokeObjectURL(a.href);
    } catch (err) { alert(t('workspace.quotationHistory.downloadFailed', locale) + '：' + friendlyError(err)); }
  };

  const handleDelete = async (id) => {
    if (!confirm(t('workspace.quotationHistory.confirmDelete', locale))) return;
    try {
      const r = await fetch(API_BASE + '/api/quotations/' + id, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + getToken() } });
      if (!r.ok) throw new Error(t('workspace.quotationHistory.deleteFailed', locale));
      fetchQuotations();
    } catch (err) { alert(t('workspace.quotationHistory.deleteFailed', locale) + '：' + friendlyError(err)); }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(t('workspace.quotationHistory.confirmBatchDelete', locale).replace('{count}', selectedIds.size))) return;
    try {
      const b = new URLSearchParams();
      b.append('ids', JSON.stringify(Array.from(selectedIds)));
      const r = await fetch(API_BASE + '/api/quotations/batch-delete', {
        method: 'POST', body: b,
        headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      if (!r.ok) throw new Error(t('workspace.quotationHistory.deleteFailed', locale));
      fetchQuotations();
    } catch (err) { alert(t('workspace.quotationHistory.deleteFailed', locale) + '：' + friendlyError(err)); }
  };

  const handleDeleteAll = async () => {
    if (quotations.length === 0) return;
    if (!confirm(t('workspace.quotationHistory.confirmDeleteAll', locale))) return;
    try {
      const ids = quotations.map(q => q.id);
      const b = new URLSearchParams();
      b.append('ids', JSON.stringify(ids));
      const r = await fetch(API_BASE + '/api/quotations/batch-delete', {
        method: 'POST', body: b,
        headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      if (!r.ok) throw new Error(t('workspace.quotationHistory.deleteFailed', locale));
      fetchQuotations();
    } catch (err) { alert(t('workspace.quotationHistory.deleteFailed', locale) + '：' + friendlyError(err)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-[var(--navy)]">{t('workspace.quotationHistory.title', locale)}</h2>
        {quotations.length > 0 && (
          <div className="flex items-center gap-2">
            {selectedIds.size > 0 && (
              <button onClick={handleBatchDelete}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-white bg-[var(--error)] hover:bg-red-700 cursor-pointer">
                {t('workspace.quotationHistory.deleteSelected', locale).replace('{count}', selectedIds.size)}
              </button>
            )}
            <button onClick={handleDeleteAll}
              className="px-3 py-1.5 rounded-lg text-xs border border-[var(--border)] text-[var(--text-secondary)] hover:bg-gray-50 cursor-pointer">
              {t('workspace.quotationHistory.deleteAll', locale)}
            </button>
          </div>
        )}
      </div>
      {loading ? (
        <div className="flex items-center justify-center py-10"><div className="w-8 h-8 border-3 border-[var(--gold)] border-t-transparent rounded-full animate-spin" /></div>
      ) : quotations.length === 0 ? (
        <div className="border border-[var(--border)] rounded-xl bg-[var(--surface)] p-10 text-center">
          <p className="text-sm text-[var(--text-secondary)]">{t('workspace.quotationHistory.empty', locale)}</p>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-2 px-1 py-1">
            <input type="checkbox" className="accent-[var(--navy)]"
              checked={quotations.length > 0 && quotations.every(q => selectedIds.has(q.id))}
              onChange={handleSelectAll} />
            <span className="text-xs text-[var(--text-secondary)]">{t('workspace.quotationHistory.selectAll', locale)}</span>
          </div>
          {quotations.map(q => (
            <div key={q.id} className={'border rounded-xl bg-[var(--surface)] p-4 flex items-center justify-between ' + (selectedIds.has(q.id) ? 'border-[var(--navy)]' : 'border-[var(--border)]')}>
              <div className="flex items-center gap-3">
                <input type="checkbox" className="accent-[var(--navy)]" checked={selectedIds.has(q.id)} onChange={() => toggleSelect(q.id)} />
                <div>
                  <p className="text-sm font-medium text-[var(--navy)]">{q.title || 'Quote #' + q.id}</p>
                  <p className="text-xs text-[var(--text-secondary)]">{q.file_name || ''} · {t('workspace.quotationHistory.productCount', locale).replace('{count}', q.model_count || '?')}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => handleDownload(q.id)} className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-xs hover:bg-gray-50 cursor-pointer">{t('workspace.quotationHistory.download', locale)}</button>
                <button onClick={() => handleDelete(q.id)} className="px-3 py-1.5 rounded-lg text-xs text-[var(--error)] hover:bg-red-50 cursor-pointer">{t('workspace.quotationHistory.delete', locale)}</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
