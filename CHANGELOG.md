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
- User onboarding card on first workspace visit
- CI workflow (backend tests + frontend lint)
- Pro upgrade email notification on webhook
- Creem subscription details (subscription_id, subscription_end) stored on upgrade

### Changed
- Register endpoint now requires email (validation + uniqueness check)
- Forgot-password page: replaced WeChat-only dead-end with email form
- Email placeholder in translations: optional → required
- Webhook handler: now writes subscription_id and subscription_end

### Security
- Rate limiting: 5/min login/register, 3/min forgot-password, 20/min parse
- HSTS: max-age=63072000; includeSubDomains; preload
- Input sanitization: html.escape on all product text fields
- IP detection: X-Forwarded-For aware rate limit key function

---

## v1.0.0 — 2026-05 ~ 2026-06

### Core
- FastAPI backend with JWT auth
- Next.js 16 frontend with i18n (zh/en)
- Dual-parser engine (universal + specialized) with scoring
- Support: Excel (.xlsx/.xls), PDF, DOCX
- Quotation generation: Excel + PDF
- PI, Packing List, Commercial Invoice (Pro)

### Features
- Anonymous homepage parse + quotation generation
- Workspace: product library, quotation history
- Smart Paste (Pro): AI text-to-products
- Creem payment integration ($9.99/mo Pro)
- Company template management
- Bank info management
- Product image matching from files
- Exchange rate integration
- Vercel Analytics
