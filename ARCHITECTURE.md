# Architecture — QuoteFlow

## Overview

QuoteFlow is a two-tier web application for automated product quotation generation from uploaded documents (Excel, PDF, DOCX).

```
┌─────────────┐     HTTPS      ┌──────────┐     HTTP      ┌──────────────┐
│   Browser    │ ◄───────────► │  Vercel   │ ◄──────────► │  Alibaba VPS  │
│  (Next.js)   │    CDN        │ (landing) │   API calls   │  (backend)    │
└─────────────┘                └──────────┘               │  FastAPI      │
                                                          │  :8000        │
                                                          │  SQLite/PG    │
                                                          └──────────────┘
```

## Frontend (landing/)

**Framework:** Next.js 16 (App Router), all pages as client components (`'use client'`).

### Component Tree

```
layout.js (html, fonts, metadata)
  └─ LocaleProvider (i18n context)
      └─ ClientLayout
          └─ ErrorBoundary
              └─ page.js  (each route)
                  ├─ Nav
                  ├─ [page content]
                  └─ Footer
```

### Key Modules

| File | Purpose |
|------|---------|
| `lib/api.js` | API base URL config |
| `lib/auth.js` | Token storage, auto-refresh on 401 |
| `lib/i18n.js` | Context-based i18n (zh/en) |
| `lib/locale.js` | Language detection (IP + localStorage) |
| `lib/errors.js` | User-friendly error messages |
| `components/ErrorBoundary.js` | Error capture + Sentry |

### Pages

| Route | Description | Auth |
|-------|-------------|:----:|
| `/` | Homepage — file upload, parse, generate quote | Optional |
| `/pricing` | Pricing — Free vs Pro comparison | No |
| `/how-it-works` | Feature walkthrough | No |
| `/login` | Login form | No |
| `/register` | Registration (username + email + password) | No |
| `/forgot-password` | Password reset (email-based) | No |
| `/reset-password` | Reset with token from email | No |
| `/workspace` | Dashboard — upload, product library, history | Required |
| `/account` | Account settings, company info, bank info | Required |
| `/terms` | Terms of Service | No |
| `/privacy` | Privacy Policy | No |

### i18n

All UI strings in `translations/{zh,en}.json`. Locale detected via:
1. `localStorage` (user preference)
2. `ip-api.com` (CN → zh, else → en)
3. Fallback: `zh`

---

## Backend (backend/)

**Framework:** FastAPI (Python), async SQLAlchemy ORM.

### API Endpoint Catalog

#### Auth (`/api/auth/`)
| Method | Path | Rate Limit | Auth |
|--------|------|:----------:|:----:|
| POST | `/register` | 5/min | No |
| POST | `/login` | 5/min | No |
| POST | `/refresh` | — | Cookie |
| PUT | `/change-password` | — | Required |
| POST | `/forgot-password` | 3/min | No |
| POST | `/reset-password` | 5/min | No |

#### Payment (`/api/payment/`)
| Method | Path | Rate Limit | Auth |
|--------|------|:----------:|:----:|
| POST | `/create-checkout` | — | Required |
| POST | `/webhook` | — | HMAC |

#### Parser (`/api/parse*`)
| Method | Path | Rate Limit | Auth |
|--------|------|:----------:|:----:|
| POST | `/parse` | 20/min | Optional |
| POST | `/parse/with-ai` | — | Optional |
| POST | `/parse-text-products` | — | Pro required |

#### Products & Quotations
| Method | Path | Auth |
|--------|------|:----:|
| GET/POST | `/api/products` | Required |
| DELETE | `/api/products/{id}` | Required |
| POST | `/api/products/batch-delete` | Required |
| GET | `/api/quotations` | Required |
| GET/DELETE | `/api/quotations/{id}` | Required |
| POST | `/api/quotation` | Optional |
| POST | `/api/quotation/pdf` | Optional |
| POST | `/api/pi` | Pro required |
| POST | `/api/packing` | Pro required |
| POST | `/api/invoice` | Pro required |

#### Config
| Method | Path | Auth |
|--------|------|:----:|
| Get/Post | `/api/template` | Required |
| POST | `/api/template/upload` | No |
| POST/GET/DELETE | `/api/template/document/{type}` | Mixed |
| POST/GET | `/api/bank/save`, `/load` | Required |
| POST | `/api/company/logo` | Required |
| GET | `/api/images` | No (path-whitelisted) |
| GET | `/api/health` | No |
| GET | `/api/exchange-rate` | No |

### Security Middleware

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Strict-Transport-Security | max-age=63072000; includeSubDomains; preload |
| CORS | Whitelist origins only |

### Database Schema

**`users` table:**
```
id, username (unique), email (unique), password_hash (bcrypt),
tier (free/pro), upload_count, upload_month, subscription_id,
subscription_end, created_at
```

**`web_products` table:** 20+ columns (model, names, specs, prices, images, carton info)

**`web_quotations` table:** user_id, product_ids (JSON), file_name, file_path, created_at

### Email System (`mailer.py`)

Three-tier delivery:
1. Resend API (`RESEND_API_KEY`)
2. SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`)
3. Noop (log only, for development)

### Rate Limiting (`slowapi`)

Per-IP rate limits using `X-Forwarded-For` header (nginx-aware).

---

## Parser Engine (product_tool/)

Dual-parser architecture with scoring:
1. **Universal parser** (`universal_parser.py`): 3-layer strategy (KV → table → content-driven)
2. **Specialized parsers**: Format-specific (Excel, DOCX, PDF)
3. **Scoring** (`score.py`): 7-level signal combination scoring → winner selected

### Supported Formats

| Format | Extensions | Parser |
|--------|-----------|--------|
| Excel | .xlsx, .xls | excel_parser_v3.py |
| Word | .docx | doc_parser.py |
| PDF | .pdf | pdf_parser.py |

---

## Infrastructure

### Production

| Component | Location | Notes |
|-----------|----------|-------|
| Frontend | Vercel | `landing/` root directory |
| Backend | Alibaba Cloud VPS (Singapore) | nginx proxy → uvicorn :8000 |
| Database | Local SQLite or PostgreSQL | Configurable via DATABASE_URL |
| CDN | Vercel Edge Network | Static assets |
| Monitoring | Sentry | Error tracking (backend + frontend) |

### CI/CD

- `.github/workflows/ci.yml`: Runs backend tests + frontend lint on PR/push
- `.github/workflows/deploy.yml`: SSH deploy to VPS on push to master

### Backups

Via cron: `sqlite3 backend/app.db ".backup backups/app-$(date +%Y%m%d).db"` (daily, 7-day retention)

---

## Key Design Decisions

1. **Dual parser + scoring** over single parser — improves accuracy by ~40%
2. **Optional auth on homepage** — allows anonymous trial without signup
3. **All client components** (`'use client'`) — simple but limits SSR/SEO. OK for tool app.
4. **SQLite as default** — zero-config for small deployments, PostgreSQL for scale
5. **httpOnly cookie refresh tokens** — prevents XSS token theft
6. **Per-IP rate limiting** — nginx-aware via X-Forwarded-For
