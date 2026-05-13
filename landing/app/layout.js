import { Noto_Sans_SC, Inter } from "next/font/google";
import "./globals.css";
import ClientLayout from "@/components/ClientLayout";

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
  title: "报价整合工具 — 上传文件，30秒生成报价单",
  description: "外贸SOHO报价工具。支持Excel/PDF/Word自动解析，一键生成带图片的报价单、PI、装箱单、商业发票。无需注册，免费体验。",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN" className={`${notoSansSC.variable} ${inter.variable}`}>
      <body className="min-h-screen flex flex-col font-sans"><ClientLayout>{children}</ClientLayout></body>
    </html>
  );
}
