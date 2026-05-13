'use client';

import { useState } from 'react';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

const steps = [
  {
    title: '上传文件',
    icon: '\uD83D\uDCE4',
    subtitle: '拖入或选择供应商文件，系统自动读取',
    items: [
      '拖拽或点击选择供应商文件，支持 Excel / PDF / Word 等常见格式',
      '无需手动整理数据，系统自动识别文件类型并提取内容',
      '一次可上传多个文件，自动合并到同一产品库',
      '上传加密处理，解析完成即删除原文件，不长期留存',
    ],
  },
  {
    title: '自动解析',
    icon: '\uD83D\uDD0D',
    subtitle: '智能识别产品信息，无需手动录入',
    items: [
      '自动识别文件中的产品型号、规格、价格等关键信息',
      '多策略智能解析，适应不同格式和排版的文件',
      '三路图片匹配引擎，自动为产品找到对应的图片',
      '多个文件间的重复产品自动去重合并',
    ],
  },
  {
    title: '全部出单',
    icon: '\uD83D\uDCC4',
    subtitle: '一份数据，生成全套外贸单据',
    items: [
      'Excel 报价单：含产品图片、公司信息、贸易术语，专业排版',
      'PDF 报价单：适合直接发送给海外客户',
      '形式发票 PI：外贸交易的标准单据',
      '装箱单 + 商业发票：完整的外贸单证体系',
      '所有单据一键生成，即下即用',
    ],
  },
];

const pipelineSteps = [
  { label: '上传文件', desc: 'Excel / PDF / Word', color: 'navy' },
  { label: '格式识别', desc: '自动检测 6 种布局', color: 'gold' },
  { label: '数据提取', desc: '三层策略评分择优', color: 'navy' },
  { label: '图片匹配', desc: '三路引擎自动配图', color: 'gold' },
  { label: '去重合并', desc: '7 步模糊去重算法', color: 'navy' },
  { label: '分类整理', desc: '自动归类到品类', color: 'gold' },
  { label: '产品入库', desc: '保存到产品库', color: 'navy' },
  { label: '一键出单', desc: '5 种单据可选', color: 'gold' },
];

const docTypes = [
  { label: 'Excel 报价单', desc: '含产品图片、公司信息、贸易术语，专业排版', free: true },
  { label: 'PDF 报价单', desc: '适合直接发送给海外客户，格式固定', free: true },
  { label: '形式发票 PI', desc: 'Proforma Invoice，外贸交易的标准单据', free: false },
  { label: '装箱单', desc: 'Packing List，含每箱重量/尺寸明细', free: false },
  { label: '商业发票', desc: 'Commercial Invoice，完整的外贸单证', free: false },
];

export default function HowItWorksPage() {
  const [expanded, setExpanded] = useState(0);

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="how-it-works" />

      <section className="flex-1 max-w-4xl mx-auto w-full px-6 pt-12 pb-20">
        {/* Header */}
        <div className="text-center mb-4">
          <h1 className="text-3xl font-bold text-[var(--navy)]">工作原理</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-2">从上传文件到生成专业外贸单据，三步完成</p>
        </div>

        {/* ─── 3-Step Timeline ─── */}
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

        {/* ─── Full Workflow Pipeline ─── */}
        <div className="mb-14">
          <h2 className="text-xl font-bold text-[var(--navy)] text-center mb-2">完整数据处理流程</h2>
          <p className="text-sm text-[var(--text-secondary)] text-center mb-8">从源文件到最终单据，每一步自动完成</p>

          {/* Desktop: horizontal flow */}
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

          {/* Mobile: vertical list */}
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

        {/* ─── Parsing Strategy Detail ─── */}
        <div className="mb-14 border border-[var(--border)] rounded-xl p-6 bg-[var(--surface)]">
          <h3 className="text-base font-bold text-[var(--navy)] mb-4 text-center">智能解析策略</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-[var(--border)] rounded-lg p-4 text-center">
              <div className="text-lg mb-2">&#128269;</div>
              <div className="font-medium text-sm text-[var(--navy)] mb-1">策略一：KV 布局检测</div>
              <p className="text-xs text-[var(--text-secondary)]">识别 "Model:" / "型号:" 标记格式，提取键值对</p>
            </div>
            <div className="border border-[var(--border)] rounded-lg p-4 text-center">
              <div className="text-lg mb-2">&#128202;</div>
              <div className="font-medium text-sm text-[var(--navy)] mb-1">策略二：表格布局</div>
              <p className="text-xs text-[var(--text-secondary)]">检测表头列映射，按列位置提取数据</p>
            </div>
            <div className="border border-[var(--border)] rounded-lg p-4 text-center">
              <div className="text-lg mb-2">&#129302;</div>
              <div className="font-medium text-sm text-[var(--navy)] mb-1">策略三：内容推断</div>
              <p className="text-xs text-[var(--text-secondary)]">分析内容模式推断列角色，兜底提取</p>
            </div>
          </div>
          <p className="text-xs text-[var(--text-secondary)] text-center mt-3">三种策略自动评分择优，选择最佳解析结果</p>
        </div>

        {/* ─── Document Types ─── */}
        <div className="mb-14">
          <h2 className="text-xl font-bold text-[var(--navy)] text-center mb-2">可生成的单据</h2>
          <p className="text-sm text-[var(--text-secondary)] text-center mb-6">一份产品数据，生成全部外贸所需单据</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {docTypes.map((doc, i) => (
              <div key={i} className="border border-[var(--border)] rounded-xl p-5 bg-[var(--surface)] flex items-start gap-4 hover:shadow-md transition-shadow">
                <div className={'w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ' + (doc.free ? 'bg-green-50' : 'bg-amber-50')}>
                  &#128196;
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--navy)]">{doc.label}</span>
                    {!doc.free && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8E1] text-[#F57F17] font-medium">Pro</span>}
                    {doc.free && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E8F5E9] text-[#2E7D32] font-medium">免费</span>}
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">{doc.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ─── CTA ─── */}
        <div className="cta-section text-center">
          <h2>准备好开始了吗？</h2>
          <p className="mt-2 mb-6">上传文件，30秒生成专业外贸报价单</p>
          <a href="/" className="inline-block px-8 py-3 rounded-xl bg-[var(--gold)] text-white text-base font-medium hover:bg-[var(--gold-light)] transition-colors">上传文件，开始体验</a>
        </div>
      </section>

      <Footer />
    </div>
  );
}
