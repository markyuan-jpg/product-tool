# 任务计划

## ✅ 已完成 (2026-06-16)

### 商业化就绪 P0
- [x] API 限流 (slowapi) — 登录/注册 5次/分, 解析 20次/分
- [x] HSTS 安全头 — 前后端均已添加
- [x] 注册加 email 必填 — 后端验证 + 邮箱唯一性检查
- [x] 邮件基础设施 — Resend/SMTP/noop 三通道
- [x] 忘记密码完整流程 — 邮件发送重置链接 → token 验证 → 设新密码
- [x] Sentry 错误监控 — 后端 sentry-sdk + 前端 ErrorBoundary 集成

### 商业化就绪 P1
- [x] 结构化日志 — LOG_JSON=1 启用 JSON 格式输出
- [x] XSS 输入清洗 — html.escape 所有文本字段
- [x] SEO 优化 — 首页/定价/工作原理页动态 meta 标签
- [x] ToS + 隐私政策 — /terms /privacy 页面 + Footer 链接
- [x] 用户引导 — 首次 workspace 显示 onboarding 卡片
- [x] CI 工作流 — backend tests + frontend lint
- [x] 支付 Webhook 邮件通知 — 升级时自动发邮件

### 文档
- [x] README.md (新建)
- [x] ARCHITECTURE.md (新建)
- [x] CHANGELOG.md (新建)
- [x] CONTRIBUTING.md (新建)
- [x] SECURITY.md (新建)
- [x] AGENTS.md 更新 (env vars)
- [x] docs/已知限制.md 更新 (安全限制)

---

## 📋 待完成

### P0 剩余
- [ ] P0-2: 后端测试 (backend/tests/)

### P2 (有用户基础后)
- [ ] Docker 化部署
- [ ] Server Components (SSR)
- [ ] 验证码 (Turnstile)
- [ ] CSRF 防护加固
- [ ] 管理后台
- [ ] 数据自动备份脚本
- [ ] 多语言完善 (lang 动态切换)
- [ ] Webhook subscription_id/subscription_end 补全 ✅ (已在本次更新完成)
