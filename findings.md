# 调研发现

## 已完成修复

### 商业化就绪审查 (2026-06-16)

发现未做商业化就绪评估。经全面审计发现 16 项缺失：

**P0 (6项):**
- 无 API 限流 → 已加 slowapi
- 无 HSTS → 已加安全头
- 注册无 email → 已改为必填
- 无邮件系统 → 已加 Resend/SMTP
- 忘记密码是死胡同 → 已完成邮件重置流程
- 无错误监控 → 已接 Sentry

**P1 (7项):**
- 日志无结构 → 已加 JSON 格式
- 无 XSS 防护 → 已加 html.escape
- SEO 缺失 → 已补 meta 标签
- 无法律文档 → 已建 ToS + 隐私
- 无用户引导 → 已加 onboarding
- CI 只有部署 → 已加测试/lint
- 支付无通知 → 已加升级邮件

**文档 (全部缺失):**
- README/ARCHITECTURE/CHANGELOG/CONTRIBUTING/SECURITY → 已新建
- AGENTS.md/已知限制.md → 已更新

---

## 历史调研 (已解决)

### PDF 图片匹配 (Phase 1)
根因：PyMuPDF 生成文件名不含型号信息
解决：改为页面位置顺序匹配 (已部署)

### 扫描 PDF 检测 (Phase 2)  
根因：扫描 PDF 无文字，三种策略均返回空
解决：检测文字总量，<50 字符时提示用户 (已部署)

### 性能优化 (Phase 3)
根因：重复 load_workbook、重复图片提取、无条件策略执行
解决：缓存 workbook、提前退出策略、统一图片提取 (已部署)
