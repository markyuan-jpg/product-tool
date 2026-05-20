'use client';

import { useState, useEffect } from 'react';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale, t } from '@/lib/i18n';

export default function HowItWorksPage() {
  const { locale, ready } = useLocale();
  const [expanded, setExpanded] = useState(0);

  useEffect(() => {
    if (!ready) return;
    document.title = t('howItWorks.title', locale);
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', t('howItWorks.subtitle', locale));
  }, [ready, locale]);

  if (!ready) return null;

  const steps = [0, 1, 2].map(i => ({
    icon: ['\uD83D\uDCE4', '\uD83D\uDD0D', '\uD83D\uDCC4'][i],
    title: t(`howItWorks.steps.${i}.title`, locale),
    subtitle: t(`howItWorks.steps.${i}.subtitle`, locale),
    items: [0, 1, 2, 3].map(j => t(`howItWorks.steps.${i}.items.${j}`, locale)).filter(x => !x.startsWith('howItWorks')),
  }));

  const pipelineSteps = [0,1,2,3,4,5,6,7].map(i => ({
    label: t(`howItWorks.pipeline.steps.${i}.label`, locale),
    desc: t(`howItWorks.pipeline.steps.${i}.desc`, locale),
    color: ['navy','gold','navy','gold','navy','gold','navy','gold'][i],
  }));

  const docTypes = [0,1,2,3,4].map(i => ({
    label: t(`howItWorks.docTypes.items.${i}.label`, locale),
    desc: t(`howItWorks.docTypes.items.${i}.desc`, locale),
    pro: t(`howItWorks.docTypes.items.${i}.pro`, locale) === 'true',
  }));

  const strategies = [0,1,2].map(i => ({
    title: t(`howItWorks.strategy.items.${i}.title`, locale),
    desc: t(`howItWorks.strategy.items.${i}.desc`, locale),
  }));

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="how-it-works" />

      <section className="flex-1 max-w-4xl mx-auto w-full px-6 pt-12 pb-20">
        <div className="text-center mb-4">
          <h1 className="text-3xl font-bold text-[var(--navy)]">{t('howItWorks.title', locale)}</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-2">{t('howItWorks.subtitle', locale)}</p>
        </div>

        {/* 3-Step Timeline */}
        <div className="timeline mb-16">
          {steps.map((step, idx) => (
            <div key={idx} className={`timeline-step ${expanded === idx ? 'active' : ''}`}>
              <div className="timeline-dot" />
              <div className="timeline-header" onClick={() => setExpanded(expanded === idx ? -1 : idx)}>
                <div className="step-icon">{step.icon}</div>
                <div>
                  <h3>{step.title}</h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">{step.subtitle}</p>
                </div>
              </div>
              {expanded === idx && (
                <div className="timeline-body">
                  <ul>{step.items.map((item, i) => <li key={i}>{item}</li>)}</ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Pipeline */}
        <div className="mb-14">
          <h2 className="text-xl font-bold text-[var(--navy)] text-center mb-2">{t('howItWorks.pipeline.title', locale)}</h2>
          <p className="text-sm text-[var(--text-secondary)] text-center mb-8">{t('howItWorks.pipeline.subtitle', locale)}</p>
          <div className="hidden md:flex items-start justify-between gap-1">
            {pipelineSteps.map((s, i) => (
              <div key={i} className="flex-1 text-center">
                <div className={'w-10 h-10 mx-auto rounded-full flex items-center justify-center text-sm font-bold text-white mb-2 ' + (s.color === 'navy' ? 'bg-[var(--navy)]' : 'bg-[var(--gold)]')}>
                  {i + 1}
                </div>
                <p className="text-xs font-medium text-[var(--navy)]">{s.label}</p>
                <p className="text-[10px] text-[var(--text-secondary)]">{s.desc}</p>
                {i < pipelineSteps.length - 1 && <div className="h-0.5 bg-[var(--border)] mt-2 mx-2" />}
              </div>
            ))}
          </div>
          <div className="md:hidden space-y-3">
            {pipelineSteps.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className={'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ' + (s.color === 'navy' ? 'bg-[var(--navy)]' : 'bg-[var(--gold)]')}>
                  {i + 1}
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--navy)]">{s.label}</p>
                  <p className="text-xs text-[var(--text-secondary)]">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategy */}
        <div className="mb-14 border border-[var(--border)] rounded-xl p-6 bg-[var(--surface)]">
          <h3 className="text-base font-bold text-[var(--navy)] mb-4 text-center">{t('howItWorks.strategy.title', locale)}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {strategies.map((s, i) => (
              <div key={i} className="border border-[var(--border)] rounded-lg p-4 text-center">
                <div className="text-lg mb-2">{['🔍', '📊', '🧠'][i]}</div>
                <div className="font-medium text-sm text-[var(--navy)] mb-1">{s.title}</div>
                <p className="text-xs text-[var(--text-secondary)]">{s.desc}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-[var(--text-secondary)] text-center mt-3">{t('howItWorks.strategy.footer', locale)}</p>
        </div>

        {/* Document Types */}
        <div className="mb-14">
          <h2 className="text-xl font-bold text-[var(--navy)] text-center mb-2">{t('howItWorks.docTypes.title', locale)}</h2>
          <p className="text-sm text-[var(--text-secondary)] text-center mb-6">{t('howItWorks.docTypes.subtitle', locale)}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {docTypes.map((doc, i) => (
              <div key={i} className="border border-[var(--border)] rounded-xl p-5 bg-[var(--surface)] flex items-start gap-4 hover:shadow-md transition-shadow">
                <div className={'w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ' + (doc.pro ? 'bg-amber-50' : 'bg-green-50')}>
                  &#128196;
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--navy)]">{doc.label}</span>
                    {doc.pro && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8E1] text-[#F57F17] font-medium">{t('howItWorks.docTypes.pro', locale)}</span>}
                    {!doc.pro && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E8F5E9] text-[#2E7D32] font-medium">{t('howItWorks.docTypes.free', locale)}</span>}
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">{doc.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Paste */}
        <div className="mb-14 border border-[var(--border)] rounded-xl p-6 bg-[var(--surface)] text-center">
          <div className="text-3xl mb-2">📋</div>
          <h3 className="text-base font-bold text-[var(--navy)] mb-2">{t('howItWorks.smartPaste.title', locale)}</h3>
          <p className="text-sm text-[var(--text-secondary)]">{t('howItWorks.smartPaste.subtitle', locale)}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">{t('howItWorks.smartPaste.desc', locale)}</p>
        </div>

        {/* CTA */}
        <div className="cta-section text-center">
          <h2>{t('howItWorks.cta.title', locale)}</h2>
          <p className="mt-2 mb-6">{t('howItWorks.cta.subtitle', locale)}</p>
          <a href="/" className="inline-block px-8 py-3 rounded-xl bg-[var(--gold)] text-white text-base font-medium hover:bg-[var(--gold-light)] transition-colors">{t('howItWorks.cta.button', locale)}</a>
        </div>
      </section>

      <Footer />
    </div>
  );
}
