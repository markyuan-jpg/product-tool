# 📚 QuoteFlow 文档导航

> 项目完整文档索引。按角色和需求分类，点击跳转。

---

## 快速入口

| 我想… | 看这个 |
|-------|--------|
| 了解这个项目是啥 | [README.md](../README.md) |
| 理解完整架构（含 API/DB/安全/解析器/数据流/部署） | **[系统架构与功能实现文档](系统架构与功能实现文档.md)** |
| 部署到服务器 | [部署指南](部署指南.md) |
| 看有哪些已知限制 | [已知限制](已知限制.md) |
| 了解产品需求 | [产品需求文档](../product_tool/产品需求文档.md) |
| 了解前端技术细节 | [前端 README](../landing/README.md) |
| 看设计规范（颜色/字体/组件） | [设计系统](../landing/docs/设计系统.md) |
| 本地开发怎么搭 | [贡献指南](../CONTRIBUTING.md) |
| 看版本更新记录 | [更新日志](../CHANGELOG.md) |
| 报告安全漏洞 | [安全策略](../SECURITY.md) |
| 日常开发快捷参考 | [AGENTS.md](../AGENTS.md) |
| AI 代理需要完整上下文 | [CLAUDE.md](../CLAUDE.md) |

---

## 文档结构（合并后）

```
product-tool/
├── README.md                          ← 项目入口
├── CLAUDE.md                          ← AI 代理上下文
├── AGENTS.md                          ← 开发者快捷参考
├── CHANGELOG.md                       ← 版本记录
├── CONTRIBUTING.md                    ← 贡献指南
├── SECURITY.md                        ← 安全策略
├── docs/
│   ├── README.md                      ← 📍 你在这里
│   ├── 系统架构与功能实现文档.md       ← ⭐ 唯一架构文档（已整合全部内容）
│   ├── 部署指南.md                    ← VPS + Vercel 部署
│   └── 已知限制.md                    ← 限制/Bug/性能
├── landing/
│   ├── README.md                      ← 前端文档
│   └── docs/设计系统.md               ← 设计规范
└── product_tool/
    ├── 产品需求文档.md                ← 中文需求
    └── REQUIREMENTS.md                ← 英文需求
```

> 以下 3 份文档已合并入 `系统架构与功能实现文档.md`，不再单独维护：
> - ~~解析器架构与配置.md~~
> - ~~架构与模块调用文档.md~~
> - ~~ARCHITECTURE.md (英文版)~~
