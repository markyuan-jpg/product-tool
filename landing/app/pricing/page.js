'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { isLoggedIn, getToken } from '@/lib/auth';
import API_BASE from '@/lib/api';
import { useLocale, t } from '@/lib/i18n';

const cell = (val, developingText) => {
  if (val === true) return <span className="text-[var(--success)] font-bold">&#10003;</span>;
  if (val === 'dev') return <span className="text-xs text-gray-400">{developingText || '开发中'}</span>;
  return <span className="text-[var(--border)]">&mdash;</span>;
};

export default function PricingPage() {
  const { locale, ready } = useLocale();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    document.title = t('pricing.title', locale);
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', t('pricing.subtitle', locale));
  }, [ready, locale]);

  if (!ready) return null;

  const tiers = [0, 1, 2].map(i => ({
    name: t(`pricing.tiers.${i}.name`, locale),
    price: i === 1 ? t('pricing.tiers.1.price', locale) : ['\u00a50', '\u00a539', '\u2014'][i],
    period: i === 1 ? t('pricing.tiers.1.period', locale) : '',
    desc: t(`pricing.tiers.${i}.desc`, locale),
    action: t(`pricing.tiers.${i}.action`, locale),
    href: i === 0 ? '/' : i === 1 ? 'mailto:yb857151464@wechat.com' : '#',
    pro: i === 1,
    highlight: i === 1 ? t('pricing.tiers.1.highlight', locale) : null,
    features: [0,1,2,3,4,5,6,7,8,9,10,11,12,13].map(j => t(`pricing.tiers.${i}.features.${j}`, locale)).filter(x => !x.startsWith('pricing.')),
  }));

  const FREE_FEATURE_ROWS = new Set([0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13]);
  const features = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14].map(i => ({
    name: t(`pricing.featureTable.rows.${i}.0`, locale),
    free: FREE_FEATURE_ROWS.has(i),
    pro: true,
    flex: i < 5 || i === 3 || i === 10 || i === 11,
  }));

  const handleProCheckout = async () => {
    if (!isLoggedIn()) {
      router.push('/login?redirect=/pricing');
      return;
    }
    setCheckoutLoading(true);
    try {
      const r = await fetch(API_BASE + '/api/payment/create-checkout', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + getToken() },
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        alert(e.detail || '创建支付会话失败');
        return;
      }
      const data = await r.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert('支付链接获取失败');
      }
    } catch (err) {
      alert('网络错误，请稍后再试');
    }
    setCheckoutLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="pricing" />

      <section className="flex-1 max-w-6xl mx-auto w-full px-6 pt-12 pb-20">
        <h1 className="text-3xl font-bold text-[var(--navy)] text-center mb-2">{t('pricing.title', locale)}</h1>
        <p className="text-sm text-[var(--text-secondary)] text-center mb-10">{t('pricing.subtitle', locale)}</p>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {tiers.map((tier, idx) => (
            <div key={idx} className={'pricing-card border rounded-xl p-8 text-center flex flex-col' + (idx === 1 ? ' border-2 border-[var(--gold)] bg-[#FFFCF5] relative' : idx === 2 ? ' border-dashed border-[var(--border)] bg-white opacity-70' : ' border-[var(--border)] bg-white')}>
              {idx === 1 && <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[var(--gold)] text-white text-xs font-medium rounded-full">{tier.highlight}</span>}
              <h3 className="text-lg font-bold text-[var(--text-secondary)] mb-2">{tier.name}</h3>
              <p className={'text-3xl font-bold mb-1 ' + (idx === 2 ? 'text-[var(--text-secondary)]' : 'text-[var(--navy)]')}>{tier.price}<span className="text-sm font-normal text-[var(--text-secondary)]">{idx === 1 ? tier.period : ''}</span></p>
              <p className="text-xs text-[var(--text-secondary)] mb-6">{tier.desc}</p>
              <div className="flex-1 space-y-2 text-left mb-6">
                {tier.features.map((f, i) => f !== 'pricing.' && (
                  <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-primary)]">
                    <span className="text-[var(--success)] font-bold">&#10003;</span> {f}
                  </div>
                ))}
              </div>
              {idx === 1 ? (
                <button onClick={handleProCheckout} disabled={checkoutLoading}
                  className="block w-full py-2.5 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 transition-colors disabled:opacity-50 cursor-pointer">
                  {checkoutLoading ? t('pricing.processing', locale) : t('pricing.subscribe', locale)}
                </button>
              ) : idx === 2 ? (
                <div className="block w-full py-2.5 rounded-lg border border-dashed border-gray-300 text-gray-400 text-sm font-medium cursor-default">
                  &#128679; {t('pricing.developing', locale)}
                </div>
              ) : (
                <a href={tier.href} className="block w-full py-2.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-sm font-medium hover:bg-gray-50 transition-colors">
                  {tier.action}
                </a>
              )}
            </div>
          ))}
        </div>

        {/* Feature comparison table */}
        <div className="border border-[var(--border)] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--navy)] text-white">
                <th className="text-left px-6 py-3 font-medium">{t('pricing.featureTable.header.0', locale)}</th>
                <th className="text-center px-4 py-3 font-medium w-28">{t('pricing.featureTable.header.1', locale)}</th>
                <th className="text-center px-4 py-3 font-medium w-28">{t('pricing.featureTable.header.2', locale)}</th>
                <th className="text-center px-4 py-3 font-medium w-28">{t('pricing.featureTable.header.3', locale)}</th>
              </tr>
            </thead>
            <tbody>
              {features.map((f, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-3 text-[var(--text-primary)]">{f.name}</td>
                  <td className="text-center px-4 py-3">{cell(f.free, t('pricing.developing', locale))}</td>
                  <td className="text-center px-4 py-3">{cell(true, '')}</td>
                  <td className="text-center px-4 py-3">{cell(f.flex ? 'dev' : false, t('pricing.developing', locale))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Footer />
    </div>
  );
}
