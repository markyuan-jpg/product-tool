import { Noto_Sans_SC, Inter } from "next/font/google";
import "./globals.css";
import ClientLayout from "@/components/ClientLayout";
import { Analytics } from '@vercel/analytics/next';

const notoSansSC = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-noto-sans",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
});

export const metadata = {
  title: "报价整合工具 — Excel/PDF 自动提取产品，一键生成外贸报价单",
  description: "上传Excel、PDF或Word，自动提取产品型号、规格、价格，30秒生成报价单。支持产品库管理、形式发票PI、装箱单。外贸SOHO免费使用。",
  openGraph: {
    title: "报价整合工具",
    description: "上传Excel/PDF/Word，30秒自动解析出产品规格价格，一键生成外贸报价单",
    url: "https://quotation-tool.vercel.app",
    siteName: "报价整合工具",
    locale: "zh_CN",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "报价整合工具",
    description: "上传文件，30秒生成报价单",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN" className={`${notoSansSC.variable} ${inter.variable}`}>
      <body className="min-h-screen flex flex-col font-sans">
        <ClientLayout>{children}</ClientLayout>
        <Analytics />
      </body>
    </html>
  );
}
