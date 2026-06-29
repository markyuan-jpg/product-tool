# Changelog

All notable changes to QuoteFlow.

---

## [Unreleased]

### Added
- Rate limiting on auth & parse endpoints (slowapi)
- Email field required on registration
- Password reset flow (forgot-password + reset-password with email)
- Email infrastructure (Resend/SMTP/noop)
- HSTS security header (backend + frontend)
- Sentry error monitoring (backend + frontend)
- Structured JSON logging (opt-in via LOG_JSON=1)
- XSS input sanitization on product data
- SEO meta tags on homepage
- Terms of Service page
- Privacy Policy page
- Footer links to ToS and Privacy
- CI workflow (backend tests + frontend lint)
- Pro upgrade email notification on webhook
- Creem subscription details (subscription_id, subscription_end) stored on upgrade
- **Anonymous mode**: GuestUser + X-Session-ID header replaces JWT auth for workspace (no login required)
- **DB auto-init**: CREATE TABLE IF NOT EXISTS for web_products + web_quotations (no manual setup needed)
- **Multi-image extraction**: three-way merge (openpyxl + DISPIMG + drawing) with || concatenation, multi-column support
- **Multi-image display**: +N badge on thumbnail, click to open gallery in new window
- **Cross-origin session**: X-Session-ID header in localStorage bypasses cross-subdomain cookie restrictions
- **CSP ip-api.com whitelist**: language detection no longer blocked
- **Cookie cross-subdomain**: SameSite=None + domain=.quoteflow.it.com
- **Formula column detection**: scan first 15 rows for = prefix, skip DISPIMG/WPS image columns
- **Order number filter**: known document prefixes only (PO/SO/CO/DO/WO/IV/INV/CT/CN/QT/RFQ/PI/DN/GRN)
- **Dimension extractor**: L×W×H/Dia×H extraction from spec text, normalized to mm
- **New COLUMN_SIGNALS**: brand, cert, hscode, lead_time, warranty, barcode, origin + MOQ completion

### Changed
- Register endpoint now requires email (validation + uniqueness check)
- Forgot-password page: replaced WeChat-only dead-end with email form
- Email placeholder in translations: optional → required
- Webhook handler: now writes subscription_id and subscription_end
- **Workspace**: anonymous mode — no login required, GuestUser with tier='pro'
- **All endpoints**: require_pro made no-op; check_upload_limit always true; increment_upload no-op
- **All workspace fetch**: Authorization: Bearer removed, replaced with X-Session-ID + credentials:'include'
- **All 401→login redirects**: removed from workspace
- **Nav**: simplified to Home/HowItWorks/Workspace + language toggle only
- **Smart Paste tab**: removed from workspace UI (DeepSeek API not shared publicly)
- **Onboarding card**: removed (was causing showOnboarding is not defined error)
- **Usage bar**: removed from workspace
- **Image extraction**: _detect_image_column returns list (multi-column), DISPIMG column filter removed
- **Image tolerance**: 0 for DISPIMG/drawing (exact match), 1 for openpyxl
- **image.py three-way merge**: concatenate with set dedup instead of update overwrite
- **Merge cell fix**: _get_cell_val checks actual cell value first, merge propagation as fallback
- **Spec threshold**: lowered 30→15 chars + number+unit pattern detection
- **Price reasonableness**: removed $1-$9 exclusion, min lowered to 0.01
- **Empty ratio fix**: counts ≤-2 as noise (was ≤-3)
- **Chinese text filter**: threshold 8→20 chars, skip if valid model present
- **Skip word matching**: substring (in) → word boundary (\b)

### Security
- Rate limiting: 5/min login/register, 3/min forgot-password, 20/min parse
- HSTS: max-age=63072000; includeSubDomains; preload
- Input sanitization: html.escape on all product text fields
- IP detection: X-Forwarded-For aware rate limit key function
- **Session**: X-Session-ID header (not cookie) for cross-origin safety

### Removed
- **Smart Paste UI**: tab removed from workspace (DeepSeek API not shared publicly)
- **Onboarding card**: removed due to JS error
- **Usage bar**: removed from workspace
- **Pro locks**: all require_pro calls made no-ops

---

## v1.0.0 — 2026-05 ~ 2026-06

### Core
- FastAPI backend with JWT auth
- Next.js 16 frontend with i18n (zh/en)
- Dual-parser engine (universal + specialized) with scoring
- Support: Excel (.xlsx/.xls), PDF, DOCX
- Quotation generation: Excel + PDF
- PI, Packing List, Commercial Invoice

### Features
- Anonymous homepage parse + quotation generation
- Workspace: product library, quotation history
- Smart Paste (AI text-to-products) — later disabled
- Creem payment integration ($9.99/mo Pro)
- Company template management
- Bank info management
- Product image matching from files
- Exchange rate integration
- Vercel Analytics
