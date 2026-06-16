'use client';

import Nav from '@/components/Nav';
import Footer from '@/components/Footer';
import { useLocale } from '@/lib/i18n';

const content = {
  zh: {
    title: '隐私政策',
    lastUpdated: '最后更新：2026年6月16日',
    sections: [
      { h: '1. 信息收集', p: '我们收集以下信息：注册时提供的用户名和邮箱地址；使用服务时上传的文件内容（仅用于解析产品信息，原始文件不长期存储）；通过 Vercel Analytics 收集的匿名页面访问统计。' },
      { h: '2. 信息使用', p: '我们使用您提供的信息来：提供产品解析和报价单生成服务；发送密码重置邮件；在您升级为 Pro 时发送确认通知；改进服务质量。' },
      { h: '3. 信息存储', p: '用户数据存储在阿里云服务器（新加坡节点）的 SQLite 或 PostgreSQL 数据库中。文件上传后处理后即被删除，仅保留提取的产品数据。' },
      { h: '4. 信息分享', p: '我们不会将您的个人信息或产品数据出售、出租或分享给第三方，除非：获得您的明确同意；或法律要求。' },
      { h: '5. Cookie', p: '我们仅使用必要的身份验证 Cookie（httpOnly 的 refresh_token），用于保持登录状态。不使用跟踪 Cookie 或广告 Cookie。' },
      { h: '6. 第三方服务', p: '本服务使用以下第三方服务：Creem — 处理支付（隐私政策：creem.io/privacy）；Vercel — 前端托管和页面访问统计（隐私政策：vercel.com/legal/privacy-policy）；Resend — 发送邮件通知（如配置）。' },
      { h: '7. 数据安全', p: '我们采取合理措施保护您的数据，包括：密码使用 bcrypt 加密存储；API 通信通过 HTTPS 加密；定期备份数据库。但请注意，任何网络传输方法都不是 100% 安全的。' },
      { h: '8. 数据删除', p: '您可以随时联系我们删除您的账户和所有相关数据。Pro 订阅取消后，您的账户转为免费账户，数据保留。主动要求删除账户时，所有数据将永久删除。' },
      { h: '9. 政策变更', p: '我们可能会更新本隐私政策。重大变更会通过邮件或在网站上通知。' },
      { h: '10. 联系方式', p: '隐私相关问题请联系：support@quoteflow.it.com。' },
    ],
  },
  en: {
    title: 'Privacy Policy',
    lastUpdated: 'Last updated: June 16, 2026',
    sections: [
      { h: '1. Information We Collect', p: 'We collect: username and email address provided during registration; file content uploaded when using the service (used only for product data extraction; original files are not stored long-term); anonymous page analytics via Vercel Analytics.' },
      { h: '2. How We Use Information', p: 'We use your information to: provide product parsing and quotation generation; send password reset emails; send upgrade confirmation when you subscribe to Pro; improve service quality.' },
      { h: '3. Data Storage', p: 'User data is stored on Alibaba Cloud servers (Singapore region) in SQLite or PostgreSQL databases. Uploaded files are processed and deleted, with only extracted product data retained.' },
      { h: '4. Information Sharing', p: 'We do not sell, rent, or share your personal information or product data with third parties, except: with your explicit consent; or as required by law.' },
      { h: '5. Cookies', p: 'We use only necessary authentication cookies (httpOnly refresh_token) to maintain login state. No tracking or advertising cookies are used.' },
      { h: '6. Third-Party Services', p: 'This service uses: Creem for payment processing (privacy policy: creem.io/privacy); Vercel for frontend hosting and page analytics (privacy policy: vercel.com/legal/privacy-policy); Resend for email notifications (if configured).' },
      { h: '7. Data Security', p: 'We take reasonable measures to protect your data, including: bcrypt-hashed password storage; HTTPS encryption; periodic database backups. However, no transmission method is 100% secure.' },
      { h: '8. Data Deletion', p: 'You may contact us at any time to delete your account and all associated data. Upon Pro cancellation, your account reverts to Free and data is retained. Upon explicit account deletion request, all data is permanently deleted.' },
      { h: '9. Policy Changes', p: 'We may update this privacy policy. Material changes will be notified via email or on the website.' },
      { h: '10. Contact', p: 'For privacy-related inquiries, contact support@quoteflow.it.com.' },
    ],
  },
};

export default function PrivacyPage() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  const c = content[locale] || content.zh;

  return (
    <div className="min-h-screen flex flex-col">
      <Nav current="privacy" />
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
