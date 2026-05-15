'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { isLoggedIn, getToken } from '@/lib/auth';
import API_BASE from '@/lib/api';

const tiers = [
  {
    name: '免费体验',
    price: '\u00a50',
    desc: '无需注册，即开即用',
    action: '开始体验',
    href: '/',
    pro: false,
    features: ['上传解析 Excel / PDF / Word', '生成 Excel 报价单', '生成 PDF 报价单', '图片自动匹配嵌入', '自动货币检测与换算'],
  },
  {
    name: '专业版 Pro',
    price: '\u00a539',
    period: '/月',
    desc: '早鸟价·名额有限，后续恢复 \u00a569/月',
    action: '联系订阅',
    href: 'mailto:yb857151464@wechat.com',
    pro: true,
    highlight: '早鸟价',
    features: ['上传解析 Excel / PDF / Word', '生成 Excel 报价单', '生成 PDF 报价单', '图片自动匹配嵌入', '产品库持久化管理', '报价历史管理', 'FOB / CIF / DDP 贸易术语', '中英双语自动翻译', '形式发票 PI', '装箱单 + 商业发票', '不限产品数量', '公司信息配置', '实时汇率换算', '报价模板自适应'],
  },
  {
    name: '按需付费',
    price: '—',
    desc: '按使用量计费',
    action: '功能开发中',
    href: '#',
    pro: false,
    disabled: true,
    features: ['按解析文件数计费', '按生成单据数计费', '无需月费，用多少付多少'],
  },
];

const features = [
  { name: '上传解析 Excel / PDF / Word', free: true, pro: true, flex: true },
  { name: '生成 Excel 报价单', free: true, pro: true, flex: true },
  { name: '产品库持久化管理', free: false, pro: true, flex: true },
  { name: '报价历史管理', free: false, pro: true, flex: true },
  { name: '图片智能匹配', free: true, pro: true, flex: true },
  { name: 'FOB / CIF / DDP 贸易术语', free: false, pro: true, flex: false },
  { name: '中英双语自动翻译', free: false, pro: true, flex: false },
  { name: 'PDF 报价单', free: true, pro: true, flex: false },
  { name: '形式发票 PI', free: false, pro: true, flex: false },
  { name: '装箱单 + 商业发票', free: false, pro: true, flex: false },
  { name: '不限产品数量', free: false, pro: true, flex: true },
  { name: '公司信息配置', free: false, pro: true, flex: true },
  { name: '实时汇率换算', free: false, pro: true, flex: false },
  { name: '报价模板自适应', free: false, pro: true, flex: false },
];

const cell = (val) => {
  if (val === true) return <span className="text-[var(--success)] font-bold">&#10003;</span>;
  if (val === '开发中') return <span className="text-xs text-gray-400">开发中</span>;
  return <span className="text-[var(--border)]">&mdash;</span>;
};

export default function PricingPage() {
  useEffect(() => {
    document.title = '定价方案 — 报价整合工具 免费版和专业版';
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', '免费版200个产品，适合个人SOHO。专业版不限数量，解锁全部单据。14天无条件退款。');
  }, []);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const router = useRouter();

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
        <h1 className="text-3xl font-bold text-[var(--navy)] text-center mb-2">定价与功能对比</h1>
        <p className="text-sm text-[var(--text-secondary)] text-center mb-10">选择适合你的方案</p>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {/* Free tier */}
          <div className="pricing-card border border-[var(--border)] rounded-xl p-8 bg-white text-center flex flex-col">
            <h3 className="text-lg font-bold text-[var(--navy)] mb-2">{tiers[0].name}</h3>
            <p className="text-3xl font-bold text-[var(--navy)] mb-1">{tiers[0].price}</p>
            <p className="text-xs text-[var(--text-secondary)] mb-6">{tiers[0].desc}</p>
            <div className="flex-1 space-y-2 text-left mb-6">
              {tiers[0].features.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-primary)]">
                  <span className="text-[var(--success)] font-bold">&#10003;</span> {f}
                </div>
              ))}
            </div>
            <a href={tiers[0].href} className="block w-full py-2.5 rounded-lg border border-[var(--navy)] text-[var(--navy)] text-sm font-medium hover:bg-gray-50 transition-colors">
              {tiers[0].action}
            </a>
          </div>

          {/* Pro tier */}
          <div className="pricing-card pro border-2 border-[var(--gold)] rounded-xl p-8 bg-[#FFFCF5] text-center flex flex-col relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[var(--gold)] text-white text-xs font-medium rounded-full">{tiers[1].highlight}</span>
            <h3 className="text-lg font-bold text-[var(--navy)] mb-2">{tiers[1].name}</h3>
            <p className="text-3xl font-bold text-[var(--navy)] mb-1">{tiers[1].price}<span className="text-sm font-normal text-[var(--text-secondary)]">{tiers[1].period}</span></p>
            <p className="text-xs text-[var(--text-secondary)] mb-6">{tiers[1].desc}</p>
            <div className="flex-1 space-y-2 text-left mb-6">
              {tiers[1].features.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-primary)]">
                  <span className="text-[var(--success)] font-bold">&#10003;</span> {f}
                </div>
              ))}
            </div>
            <button onClick={handleProCheckout} disabled={checkoutLoading}
              className="block w-full py-2.5 rounded-lg bg-[var(--gold)] text-white text-sm font-medium hover:bg-[var(--gold)]/90 transition-colors disabled:opacity-50 cursor-pointer">
              {checkoutLoading ? '处理中...' : '订阅专业版'}
            </button>
          </div>

          {/* Pay-as-you-go tier */}
          <div className="pricing-card border border-dashed border-[var(--border)] rounded-xl p-8 bg-white text-center flex flex-col opacity-70">
            <h3 className="text-lg font-bold text-[var(--text-secondary)] mb-2">{tiers[2].name}</h3>
            <p className="text-3xl font-bold text-[var(--text-secondary)] mb-1">{tiers[2].price}</p>
            <p className="text-xs text-[var(--text-secondary)] mb-6">{tiers[2].desc}</p>
            <div className="flex-1 space-y-2 text-left mb-6">
              {tiers[2].features.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-primary)]">
                  <span className="text-[var(--gold)] font-bold">&#9888;</span> {f}
                </div>
              ))}
            </div>
            <div className="block w-full py-2.5 rounded-lg border border-dashed border-gray-300 text-gray-400 text-sm font-medium cursor-default">
              &#128679; 功能正在开发中
            </div>
          </div>
        </div>

        {/* Feature comparison table */}
        <div className="border border-[var(--border)] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--navy)] text-white">
                <th className="text-left px-6 py-3 font-medium">功能</th>
                <th className="text-center px-4 py-3 font-medium w-28">免费体验</th>
                <th className="text-center px-4 py-3 font-medium w-28">专业版 Pro</th>
                <th className="text-center px-4 py-3 font-medium w-28">按需付费</th>
              </tr>
            </thead>
            <tbody>
              {features.map((f, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-3 text-[var(--text-primary)]">{f.name}</td>
                  <td className="text-center px-4 py-3">{cell(f.free)}</td>
                  <td className="text-center px-4 py-3">{cell(f.pro)}</td>
                  <td className="text-center px-4 py-3">{cell(f.flex ? '开发中' : false)}</td>
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
