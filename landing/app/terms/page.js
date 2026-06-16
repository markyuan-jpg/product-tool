'use client';

import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale } from '@/lib/i18n';

const content = {
  zh: {
    title: '服务条款',
    lastUpdated: '最后更新：2026年6月16日',
    sections: [
      { h: '1. 接受条款', p: '使用 QuoteFlow（以下简称"本服务"）即表示您同意遵守本服务条款。如果您不同意，请勿使用本服务。' },
      { h: '2. 服务描述', p: 'QuoteFlow 提供产品报价单在线生成工具，包括但不限于：文件上传解析、产品管理、报价单生成等功能。部分高级功能需付费使用。' },
      { h: '3. 用户账户', p: '您需提供准确的注册信息（用户名、邮箱），并对账户安全负责。禁止共享账户或将账户转让他人使用。' },
      { h: '4. 免费与专业版', p: '免费版用户每月可上传 20 个文件，最多保存 200 个产品。专业版用户无此限制且可使用智能粘贴、PI 等高级功能。价格以定价页面为准。' },
      { h: '5. 付款与退款', p: '专业版订阅通过 Creem 支付处理。订阅费用不予退还（部分退款请求请发邮件至 support@quoteflow.it.com 协商）。' },
      { h: '6. 用户内容', p: '您上传的文件仅用于生成报价单，系统不会将您的产品数据分享给第三方。您保留对上传内容的所有权利。' },
      { h: '7. 禁止行为', p: '禁止上传包含恶意代码的文件、禁止试图攻击或破解本服务、禁止批量注册或滥用 API。' },
      { h: '8. 终止服务', p: '我们保留在任何时候暂停或终止违规账户的权利。专业版用户账户被终止时，剩余订阅费用不予退还。' },
      { h: '9. 免责声明', p: '本服务按"现状"提供，不保证无错误或不中断。因使用本服务产生的任何直接或间接损失，我们不承担赔偿责任。' },
      { h: '10. 条款变更', p: '我们可能随时修改本条款，修改后的条款发布即生效。继续使用本服务即表示您接受修改后的条款。' },
      { h: '11. 联系方式', p: '如有任何问题，请发送邮件至 support@quoteflow.it.com。' },
    ],
  },
  en: {
    title: 'Terms of Service',
    lastUpdated: 'Last updated: June 16, 2026',
    sections: [
      { h: '1. Acceptance', p: 'By using QuoteFlow ("the Service"), you agree to these Terms of Service. If you do not agree, do not use the Service.' },
      { h: '2. Service Description', p: 'QuoteFlow provides an online product quotation generator, including file upload parsing, product management, quotation generation, and related features. Some advanced features require a paid subscription.' },
      { h: '3. User Accounts', p: 'You must provide accurate registration information (username, email) and are responsible for account security. Account sharing or transfer is prohibited.' },
      { h: '4. Free & Pro Plans', p: 'Free users have a monthly upload limit of 20 files and can save up to 200 products. Pro users have no such limits and can access Smart Paste, PI, and other advanced features. Pricing is as shown on the pricing page.' },
      { h: '5. Payments & Refunds', p: 'Pro subscriptions are processed via Creem. Subscription fees are non-refundable (partial refund requests may be emailed to support@quoteflow.it.com for consideration).' },
      { h: '6. User Content', p: 'Files you upload are used solely for quotation generation. We do not share your product data with third parties. You retain all rights to your uploaded content.' },
      { h: '7. Prohibited Conduct', p: 'Uploading files containing malicious code, attempting to attack or crack the Service, bulk registration, or API abuse is prohibited.' },
      { h: '8. Termination', p: 'We reserve the right to suspend or terminate accounts that violate these terms. Pro subscriptions terminated for violations are not eligible for refunds.' },
      { h: '9. Disclaimer', p: 'The Service is provided "as is" without warranties of any kind. We are not liable for any direct or indirect damages arising from use of the Service.' },
      { h: '10. Changes', p: 'We may modify these terms at any time. Changes are effective upon posting. Continued use constitutes acceptance.' },
      { h: '11. Contact', p: 'For questions, email support@quoteflow.it.com.' },
    ],
  },
};

export default function TermsPage() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  const c = content[locale] || content.zh;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="terms" />
      <main className="flex-1 max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-[var(--navy)] mb-2">{c.title}</h1>
        <p className="text-sm text-[var(--text-secondary)] mb-8">{c.lastUpdated}</p>
        <div className="space-y-6">
          {c.sections.map((s, i) => (
            <div key={i}>
              <h2 className="text-lg font-semibold text-[var(--navy)] mb-2">{s.h}</h2>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{s.p}</p>
            </div>
          ))}
        </div>
      </main>
      <Footer />
    </div>
  );
}
