# QuoteFlow 代码审查报告

> 审查时间：2026-06-25
> 审查方法：系统性全维度审查（见 `docs/审查清单.md`）

---

## 一、审查结果总览

### ✅ 通过项

| 维度 | 状态 | 说明 |
|------|------|------|
| 架构设计 | ✅ | 前后端分离，FastAPI+Next.js，双解析器+评分机制 |
| API安全 | ✅ | CORS白名单、HSTS、输入清洗、限流已配置 |
| 错误监控 | ✅ | Sentry已集成 |
| CI/CD | ✅ | GitHub Actions自动测试+部署 |
| 文档完整性 | ✅ | README/ARCHITECTURE/CHANGELOG等齐全 |
| 国际化 | ✅ | 中英文双语，IP自动检测 |

### ❌ 发现的问题

按严重程度从高到低排列：

---

## 二、P0 — 必须修复（影响核心功能）

### P0-1：PDF/Excel导出中文乱码

**文件：** `product_tool/src/output/pi_generator.py`（第18行）
**文件：** `product_tool/src/output/pdf_generator.py`

**问题描述：**
所有导出的Excel/PDF文档标题字体使用 `Font(name='Arial')`。Arial字体不包含中文字形，导出的报价单/PI/Invoice中所有中文字段会显示为方框或乱码。

**影响范围：**
- PI生成（pi_generator.py）
- 报价单生成（quotation_excel.py）
- PDF生成（pdf_generator.py）
- 装箱单生成（packing/generator.py）

**修复方案：**
```python
# 替换前
FONT_TITLE = Font(name='Arial', size=16, bold=True)

# 替换后 — 使用支持中文的字体
FONT_TITLE = Font(name='Microsoft YaHei', size=16, bold=True)
# 或指定回退字体链
FONT_TITLE = Font(name='Microsoft YaHei', size=16, bold=True)
```
同时检查 `doc_shared.py` 中的字体配置。

---

### P0-2：首页无Demo按钮，用户需上传文件才能看到效果

**文件：** `landing/app/page.js`

**问题描述：**
用户打开首页后只能看到一个上传区域，必须先拖一个文件才能知道工具是否有用。这导致跳出率极高——用户不知道"这工具到底是干啥的，效果怎样"就走了。

**修复方案：**
在首页Hero区域下方增加一个"试试Demo"按钮，点击后加载一份预设的样例会生成报价单效果展示，让用户在上传前就看到价值。

```jsx
// 在首页添加
<button onClick={handleDemoClick}>
  🎯 试试Demo（无需上传）
</button>
```

---

## 三、P1 — 重要（影响留存和体验）

### P1-1：错误提示全部使用 alert() 弹窗

**文件：** `landing/app/page.js`（多处，如第76、88、142、158行）

**问题描述：**
解析失败、生成失败、格式不正确等所有错误都使用浏览器原生 `alert()` 弹窗。用户体验差、无法提供操作指引、用户不知道下一步该做什么。

**影响文件：**
- `landing/app/page.js` — 多处alert调用
- `landing/app/workspace/page.js` — 可能需要同步修改

**修复方案：**
将alert替换为页面内嵌的Toast通知或错误提示条（ErrorBanner组件），并附带建议操作。

---

### P1-2：解析结果异常时无降级体验

**文件：** `landing/app/page.js`（第83-85行）

**问题描述：**
当服务端返回空数据或解析失败时，前端没有显示"部分解析成功，请手动修正"的界面。用户无法介入修正，只能放弃。

**修复方案：**
解析完成后增加一个"解析结果预览"步骤，让用户可以：
- 手动编辑解析结果
- 添加缺失字段
- 重新提交修正后的数据
- 删除错误识别的产品

---

### P1-3：上传限制提示不清晰

**文件：** `landing/app/page.js`（第33、72-76行）

**问题描述：**
`MAX_FREE_FILES = 3` 的免费限制是在代码里硬编码的。用户上传第4个文件时直接无反应，没有任何提示说明为什么不能上传或如何解锁。

**修复方案：**
在上传区显示"已使用 X/3 次免费解析"，用完后显示"已用尽免费次数，注册Pro用户解锁无限解析"引导。

---

### P1-4：60s解析超时无重试机制

**文件：** `landing/app/page.js`（第80行）

**问题描述：**
解析请求硬超时60秒，超时后直接报错。大文件或高延迟场景下用户无法重试，也没有断点续传。

**修复方案：**
增加自动重试逻辑（1-2次），超时后提示"解析较慢，可能是文件较大，是否重试？"

---

## 四、P2 — 建议优化（有用户基础后做）

| 编号 | 问题 | 文件 |
|------|------|------|
| P2-1 | 解析API `/api/parse` 没有分页，一次性返回所有数据 | `backend/main.py` |
| P2-2 | 前端静态资源没有CDN缓存策略 | `landing/next.config.mjs` |
| P2-3 | 图片提取后存储为临时文件没有清理机制 | `product_tool/src/core/image.py` |
| P2-4 | 缺少文件大小限制校验（超大PDF会OOM） | `backend/main.py` |
| P2-5 | 注册页面缺少密码强度提示 | `landing/app/register/page.js` |
| P2-6 | Docker化部署缺失 | — |

---

## 五、风险预警

| 风险 | 说明 |
|------|------|
| 字体授权 | 使用"Microsoft YaHei"需确保部署环境有该字体（Windows Server自带，Linux需安装） |
| 文件膨胀 | temp_images/目录已积累大量临时文件，需定期清理 |
| Openpyxl性能 | 大Excel文件（>10MB）处理耗时，需考虑异步队列 |
