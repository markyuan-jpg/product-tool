# QuoteFlow 系统性代码审查报告

> 审查时间：2026-06-29
> 审查方法：UX流程 / 核心功能 / 安全合规 / 边界异常 / 部署运维 五维度独立审查
> 审查范围：D:\Projects\product-tool 全项目

---

## 一、P0 — 必须修复（运行时崩溃 / 安全漏洞）

### P0-1：`/api/quotation/pdf` 端点运行时崩溃

**文件：** `backend/main.py` 行 1988

```python
user = await get_current_user_optional(authorization, db)
```

`authorization` 在函数作用域内未定义，每次调用必然抛出 `NameError`。

**影响：** PDF 报价单生成功能完全不可用。

**修复：** 替换为 `get_session_id` 或移除该行（当前匿名模式不需要 JWT 验证）。

---

### P0-2：`/api/pi` 端点运行时崩溃（4 个未定义变量）

**文件：** `backend/main.py`

| 行 | 变量 | 问题 |
|-----|------|------|
| 2062 | `bank_address` | 从未定义。仅在 `/api/invoice` 中作为 Form 参数存在，未传入 `generate_pi` |
| 2066 | `bank_swift` | 同上，从未定义 |
| 2088 | `port_destination` | 从未定义。函数签名中没有此参数，也未在其他地方声明 |
| 2090 | `brand_name` | 从未定义 |

```python
# 行 2062 — bank_address 未定义
if bank_address: seller_config['bank']['bank_address'] = bank_address

# 行 2066 — bank_swift 未定义
if bank_swift: seller_config['bank']['swift_code'] = bank_swift

# 行 2088-2090 — port_destination, brand_name 未定义
port_destination=port_destination,
brand_name=brand_name,
```

**影响：** PI 形式发票生成功能完全不可用。

**修复：** 将 `bank_address`、`bank_swift`、`port_destination`、`brand_name` 添加为 Form 参数，或从 `bank_info` JSON 中提取，或设默认值 `""`。

---

### P0-3：`/api/packing` 和 `/api/invoice` 端点运行时崩溃

**文件：** `backend/main.py` 行 2193、2196（packing）；行 2297、2300（invoice）

```python
# 行 2193
if _pro_user:
    from product_repo import save_quotation
    pk_qid = save_quotation(_pro_user.id, ...)   # _pro_user 未定义 → NameError
```

`_pro_user` 变量从未声明。正确变量应为 `user`（类型为 `GuestUser`）。

**影响：** 装箱单和商业发票生成崩溃 + 不会自动保存到报价历史。

**修复：** 替换 `_pro_user` 为 `user`。

---

### P0-4：支付 Webhook 签名验证可被绕过

**文件：** `backend/payment.py` 行 88-90

```python
if not CREEM_WEBHOOK_SECRET:
    logger.warning("Creem webhook secret not configured, skipping verification")
    return True  # ← 空密钥时直接接受任何请求
```

当 `CREEM_WEBHOOK_SECRET` 环境变量为空时（当前休眠状态下的默认情况），**任何人发送的 webhook 请求都会被当作有效**。攻击者可伪造 `checkout.completed` 事件获取 Pro 权限。

**影响：** 认证绕过 → 未授权 Pro 升级。

**修复：** 改为 `return False`，或等待恢复付费功能时再启用。同时建议检查 webhook 事件类型有效性。

---

### P0-5：CSP `unsafe-eval` 削弱 XSS 防护

**文件：** `landing/next.config.mjs` 行 10

```
script-src 'self' 'unsafe-inline' 'unsafe-eval';
```

`unsafe-eval` 允许页面执行 `eval()`、`new Function()`、`setTimeout(string)` 等动态代码。这大幅弱化了 CSP 对 XSS 攻击的防护，使攻击者能在注入脚本后执行任意代码。

**影响：** XSS 攻击面显著扩大。

**修复：** 移除 `'unsafe-eval'`；若确属某依赖所需，使用 `'sha256-...'` 哈希白名单替代。

---

### P0-6：`quotation_excel.py` 4 处字体漏设（中文乱码）

**文件：** `product_tool/src/output/quotation_excel.py`

| 行 | 代码 | 漏了什么 |
|-----|------|---------|
| 599 | `Font(bold=True, size=9)` | 缺 `name='Microsoft YaHei'` |
| 601 | `Font(size=9)` | 缺 `name='Microsoft YaHei'` |
| 1004 | `Font(size=9, color='333333')` | 缺 `name='Microsoft YaHei'` |
| 1112 | `Font(bold=True)` | 缺 `name='Microsoft YaHei'` |

这些位置的字体回退到 openpyxl 默认字体（Calibri），中文内容在无 CJK 字形的系统上会显示为方框。

**影响：** 报价单中部分中文文字乱码（信息标签行、说明文字、Raw Data 表头）。

**修复：** 4 处补上 `name='Microsoft YaHei'`。

---

### P0-7：`pdf_generator.py` CJK 字体只注册一个变体

**文件：** `product_tool/src/output/pdf_generator.py` 行 125-143

```python
for path in [font_path_1, font_path_2, ...]:
    if os.path.exists(path):
        if 'bd' in path or 'bold' in path.lower():
            pdfmetrics.registerFont(TTFont('CBF', path))
            _cn_font_bold = 'CBF'
        else:
            pdfmetrics.registerFont(TTFont('CF', path))
            _cn_font = 'CF'
        break  # ← 找到任意一个就退出
```

问题是 `break` 导致只注册第一个找到的字体变体。例如先找到 `msyhbd.ttc`（粗体）→ 只注册了 `CBF`（粗体），`_cn_font` 仍为 `'Helvetica'`（无 CJK 字形）。

**影响：** PDF 报价单中中文正文显示为方框乱码。

**修复：** 将 `break` 替换为分别跟踪 bold 和 regular 的发现状态，两个都找到再退出。或至少确保 regular 优先。

---

## 二、P1 — 重要（体验 / 稳定性 / 安全加固）

### P1-1：全站 12 处 `alert()` + 6 处 `confirm()` 阻塞弹窗

**文件：** `landing/app/page.js`（3 处）、`landing/app/workspace/page.js`（15 处）

| 文件 | 行 | 场景 | 严重性 |
|------|-----|------|:---:|
| page.js | 76 | 格式校验 → 硬编码中文 `alert('仅支持 .xlsx...')`，英文用户看不懂 | 高 |
| page.js | 158 | 报价单生成失败 `alert('生成报价单失败…')` | 中 |
| page.js | 174 | 模板上传失败 `alert(friendlyError(err))` | 中 |
| workspace | 68 | 格式校验 `alert()` | 高 |
| workspace | 326 | fetchProducts 失败 → `alert()` 暴露原始 `err.message` | 高 |
| workspace | 371, 380, 1160, 1169, 1184, 1200 | 删除/下载失败 `alert()` | 中 |
| workspace | 421, 538 | 无选中产品（按钮本应 disabled） | 中 |
| workspace | 524, 630 | 导出失败 `alert()` | 中 |
| workspace | 375, 1164, 1174, 1189, 362, 399 | 删除确认 `confirm()` | 中 |

全部应替换为页面内嵌 Toast 通知组件（非阻塞、可样式化、支持操作指引）。

**影响：** 用户体验差，iOS Safari 上 `alert()` 显示为不可关闭的系统弹窗。

---

### P1-2：10/17 个 fetch 调用无超时机制

**文件：** `landing/app/workspace/page.js`

| 行 | 端点 | 风险 |
|-----|------|------|
| 97 | `/api/products/save` | 无超时 → 无限挂起 |
| 365, 377 | batch-delete / delete | 无超时 |
| 466 | `/api/bank/load` | 无超时 |
| 506 | `/api/quotations/{id}/download` | 无超时 |
| 613 | 同上（export all 循环内） | 无超时 |
| 1153 | `/api/quotations/{id}/download` | 无超时 |
| 1166, 1178, 1194 | 报价删除 | 无超时 |

另外：`landing/app/page.js` 行 142 的下载请求也无超时保护。

**影响：** 任何网络异常都会导致页面永久挂起。

**修复：** 所有 fetch 加 `AbortController` + 合理超时（保存 30s，删除 15s，下载 60s）。

---

### P1-3：输出文件无限堆积 — 磁盘泄漏

**文件：** `backend/main.py`

`OUTPUT_DIR`（`backend/outputs/`）中的文件生成后**永不清除**：
- `quotation_{ts}.xlsx`
- `PI_{ts}.xlsx`
- `packing_{ts}.xlsx`
- `invoice_{ts}.xlsx`
- `quotation_pdf_{ts}.pdf`

**影响：** 生产环境长期运行后磁盘占满。

**修复：** 加定时清理任务（cron）或保留上限（如最近 100 个文件），或每次下载后异步删除。

---

### P1-4：`temp_images/` 图片目录无限增长

**文件：** `product_tool/src/core/image.py` 行 20、103

每次解析文件提取的图片保存到 `<project_root>/temp_images/`。有内容哈希去重（同一图片不重复保存），但**永无清理机制**。

**影响：** 随着用户上传新图片，磁盘持续增长。

**修复：** 加 TTL 清理（如 7 天未访问的文件自动删除），或按总大小限制（如 500MB 上限）。

---

### P1-5：零重试逻辑

**文件：** `landing/app/page.js`、`landing/app/workspace/page.js`

所有请求失败后：
- 无自动重试（无 exponential backoff）
- 无"重试"按钮（parseError 的"重试"按钮只关闭错误，不重发请求）
- 超时后用户只能手动重复全部操作

**影响：** 网络波动或服务器短暂不可用时，用户必须重做整个流程。

---

### P1-6：Demo 按钮点一次即永久消失

**文件：** `landing/app/page.js` 行 92-106

```javascript
const [demoLoaded, setDemoLoaded] = useState(false);
const handleDemo = () => {
    if (demoLoaded) return;  // 二次点击无响应
    ...
    setDemoLoaded(true);      // 按钮永久隐藏
};
```

**影响：** 用户无法重新激活 Demo（只能刷新页面）。

**修复：** 移除 `demoLoaded` 限制，或改为"重置 Demo"按钮。

---

### P1-7：Export All 批量导出无失败汇总

**文件：** `landing/app/workspace/page.js` 行 584-632

```javascript
// 行 605 — 单项任务失败静默吞掉
} catch (e) { /* 单个失败不影响其他 */ }

// 行 622 — 下载失败静默吞掉
} catch (e) { /* ignore download errors */ }
```

5 种单据批量生成时，用户看不到"3/5 成功、2/5 失败"的汇总。

**影响：** 用户可能以为全部成功，实际部分单据缺失。

---

### P1-8：图片画廊用 `window.open().document.write()` — 极差体验

**文件：** `landing/app/workspace/page.js` 行 207、749

```javascript
const w = window.open('');
w.document.write(paths.map(pp =>
    '<img src="' + API_BASE + '/api/images/?path=' + encodeURIComponent(pp) + '" style="max-width:100%"/>'
).join(''));
```

**问题：** 无导航箭头、无键盘（Esc 关闭、←→ 翻页）、无缩放、无响应式。两个组件的 `max-width` 不一致（100% vs 90vw）。

**影响：** 多图产品查看体验极差。

---

### P1-9：多处静默失败

| 文件 | 行 | 场景 |
|------|-----|------|
| workspace/page.js | 475 | 银行信息加载失败 → 空 catch |
| workspace/page.js | 605 | export all 单文档失败 → 静默吞掉 |
| workspace/page.js | 622 | export all 下载失败 → 静默吞掉 |
| workspace/page.js | 1133 | 报价列表加载失败 → 仅 `console.error`，UI 空白 |
| backend/main.py | 1429-1436 | 图片匹配失败 → `except Exception: pass` |
| backend/main.py | 1831-1832 | 图片预缩放失败 → `except Exception: pass` |

---

### P1-10：CSP 含通配符域名

**文件：** `landing/next.config.mjs` 行 10

```
connect-src ... https://*.railway.app https://*.vercel.app
img-src ... https://*.up.railway.app
```

`*` 通配符允许连接到**任意** Railway 或 Vercel 部署，不仅限于你的应用。

**修复：** 改为具体的部署 URL。

---

### P1-11：多个端点缺少限流保护

**文件：** `backend/main.py`

| 端点 | 风险 |
|------|------|
| `/api/parse-text-products` | 无限制 → DeepSeek API 调用 DoS |
| `/api/parse/with-ai` | 无限制 → DeepSeek API 调用 DoS |
| `/api/quotation` | 无限制 → 文件系统 DoS |
| `/api/pi` `/api/packing` `/api/invoice` | 无限制 → 文件系统 DoS |
| `/api/images` | 无限制 → 带宽 DoS |

**修复：** 至少给 AI 端点加 10/min，给文档生成端点加 30/min。

---

### P1-12：删除操作无"撤销"

**文件：** `landing/app/workspace/page.js`

全部删除（产品/报价/客户）只有一个 `confirm()` 弹窗，确认后立即删除。无 Toast "已删除 N 个产品，撤销？" + 5 秒窗口。

**影响：** 误删不可逆，用户愤怒。

---

## 三、P2 — 建议优化（非紧急）

| # | 问题 | 文件 | 行 |
|---|------|------|----|
| P2-1 | CI `continue-on-error: true` — 测试/检查失败不阻断 PR merge | `.github/workflows/ci.yml` | — |
| P2-2 | HSTS header 无条件应用（含 `http://localhost:8000`）— 浏览器会拒绝 HTTP 连接 2 年 | `backend/main.py` | 298 |
| P2-3 | `_image_cache` / `_resize_cache` 内存无界增长 — 长运行进程 OOM 风险 | `product_tool/src/core/image.py` | 24, 38 |
| P2-4 | 银行信息全局共享（`data/bank_info.json`），非 per-session 隔离 | `backend/main.py` | `/api/bank/*` |
| P2-5 | Cookie domain 硬编码 `.quoteflow.it.com` — 换域名需改代码 | `backend/main.py` | 255 |
| P2-6 | 上传仅验证扩展名，无 magic byte 检查 — 可伪造扩展名 | `backend/main.py`, `landing/app/page.js` | — |
| P2-7 | Smart Paste 死代码 ~80 行未清理 | `landing/app/workspace/page.js` | 107-143, 60-64 |
| P2-8 | `FONT_TITLE_WHITE` 定义后从未使用 | `product_tool/src/output/pi_generator.py` | 25 |
| P2-9 | `handleDrop` 仅取 `files[0]` — 不支持多文件拖拽（虽然有多文件标签页） | `landing/app/page.js` | 63 |
| P2-10 | `<input type="file">` 无 `multiple` 属性 — 每次只能选一个文件 | `landing/app/page.js` | 192 |
| P2-11 | 全局异常处理器不记日志，直接暴露 `str(exc)` 给客户端 | `backend/main.py` | 261-279 |
| P2-12 | `loop.run_in_executor()` 无超时 — worker 线程可能永久挂起 | `backend/main.py` | 1357, 1428, 1434, 1836 |
| P2-13 | 上传大小限制不一致：FastAPI 100MB vs 自定义检查 50MB | `backend/main.py` | 108, 128, 201 |
| P2-14 | 后端 HTTP 响应不设 CSP header — 缺少 defense-in-depth | `backend/main.py` | — |
| P2-15 | `quotation_excel.py` 无分页 — 数百产品可能撑爆内存 | `product_tool/src/output/quotation_excel.py` | — |
| P2-16 | `quotation_excel.py` 行 638 硬编码 `data_only=True` 但无 `read_only=True` — 大文件内存占用高 | `product_tool/src/output/quotation_excel.py` | — |

---

## 四、总结

| 级别 | 数量 | 核心风险 |
|------|:---:|---------|
| **P0** | **7** | 4 个端点 NameError 崩溃 + 1 个支付认证绕过 + 1 个 CSP 弱化 + 6 处字体乱码 |
| **P1** | **12** | 全站 18 处弹窗体验差、10 个 fetch 无超时、磁盘泄漏 ×2、零重试、静默失败 ×6、CSP 通配符、限流缺失 |
| **P2** | **16** | CI 不拦截失败、内存泄漏、硬编码、死代码、字体一致性、并发安全 |

**优先修复顺序：** P0-1~4（崩溃端点）→ P0-4（支付安全）→ P0-6~7（中文乱码）→ P0-5（CSP 加固）
