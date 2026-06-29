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
| `lib/auth.js` | Token storage & refresh (dormant, not used by workspace) |
| `lib/i18n.js` | Context-based i18n (zh/en) |
| `lib/locale.js` | Language detection (IP + localStorage) |
| `lib/errors.js` | User-friendly error messages |
| `components/ErrorBoundary.js` | Error capture + Sentry |

### Pages

| Route | Description | Auth |
|-------|-------------|:----:|
| `/` | Homepage — file upload, parse, generate quote | No |
| `/pricing` | Pricing — Free vs Pro comparison | No (hidden from Nav) |
| `/how-it-works` | Feature walkthrough | No |
| `/login` | Login form | No (hidden from Nav, dormant) |
| `/register` | Registration (username + email + password) | No (hidden from Nav, dormant) |
| `/forgot-password` | Password reset (email-based) | No |
| `/reset-password` | Reset with token from email | No |
| `/workspace` | Dashboard — upload, product library, history | No (GuestUser + X-Session-ID) |
| `/account` | Account settings, company info, bank info | No (hidden from Nav) |
| `/terms` | Terms of Service | No |
| `/privacy` | Privacy Policy | No |

### Session Mechanism (Anonymous Mode)

1. First visit → `crypto.randomUUID()` → `localStorage.quote_session_id`
2. Every fetch: `headers['X-Session-ID'] = sessionId` + `credentials: 'include'`
3. Backend: `GuestUser(session_id)` → `require_pro` no-op → all features open

Login/register/payment code preserved dormant. Recovery: restore Nav links + remove session middleware.

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
| POST | `/create-checkout` | — | Required (dormant) |
| POST | `/webhook` | — | HMAC (dormant) |

#### Parser (`/api/parse*`)
| Method | Path | Rate Limit | Auth |
|--------|------|:----------:|:----:|
| POST | `/parse` | 20/min | GuestUser |
| POST | `/parse/with-ai` | — | GuestUser (needs DEEPSEEK_API_KEY) |
| POST | `/parse-text-products` | — | GuestUser (needs DEEPSEEK_API_KEY) |

> `/parse-text-products` and `/parse/with-ai` exist but Smart Paste UI is removed (DeepSeek API not public).

#### Products & Quotations
| Method | Path | Auth |
|--------|------|:----:|
| GET/POST | `/api/products` | GuestUser |
| DELETE | `/api/products/{id}` | GuestUser |
| POST | `/api/products/batch-delete` | GuestUser |
| GET | `/api/quotations` | GuestUser |
| GET/DELETE | `/api/quotations/{id}` | GuestUser |
| POST | `/api/quotation` | GuestUser |
| POST | `/api/quotation/pdf` | GuestUser |
| POST | `/api/pi` | GuestUser |
| POST | `/api/packing` | GuestUser |
| POST | `/api/invoice` | GuestUser |

#### Config
| Method | Path | Auth |
|--------|------|:----:|
| Get/Post | `/api/template` | GuestUser |
| POST | `/api/template/upload` | No |
| POST/GET/DELETE | `/api/template/document/{type}` | Mixed |
| POST/GET | `/api/bank/save`, `/load` | GuestUser |
| POST | `/api/company/logo` | GuestUser |
| GET | `/api/images` | No (path-whitelisted, supports `\|\|` multi-path) |
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
> Dormant in anonymous mode. GuestUser uses UUID string as user_id.

**`web_products` table:** 20+ columns (model, names, specs, prices, images via `||` concat, carton info)

**`web_quotations` table:** user_id, product_ids (JSON), file_name, file_path, created_at

Both tables auto-created via `CREATE TABLE IF NOT EXISTS`.

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
1. **Universal parser** (`universal_parser.py`): 4-layer strategy (KV → table → content-driven → no-header) + formula column detection
2. **Specialized parsers**: Format-specific (Excel, DOCX, PDF)
3. **Scoring** (`score.py`): 7-level signal combination scoring → winner selected

### Supported Formats

| Format | Extensions | Parser |
|--------|-----------|--------|
| Excel | .xlsx, .xls | excel_parser_v3.py |
| Word | .docx | doc_parser.py |
| PDF | .pdf | pdf_parser.py |

### Image Extraction (`image.py`) — Three-way Merge

```
file.xlsx
  ├── extract_openpyxl_images()  → floating embedded images
  ├── parse_dispimg_images()     → WPS DISPIMG formula images (no column filter)
  └── parse_drawing_images()     → drawing XML anchored images
        └── _merge_rows() — set dedup + || concatenation
```

- **Multi-column detection:** `_detect_image_column()` returns list (picture/drawing/photo/image)
- **`||` concat:** same-row multi-column images joined (e.g., `img1.png||img2.png`)
- **Frontend display:** first image as thumbnail, `+N` badge, click opens gallery
- **Tolerance:** 0 for DISPIMG/drawing (exact), 1 for openpyxl

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

- `.github/workflows/ci.yml`: Runs backend tests (34) + frontend lint on PR/push

### Backups

Via cron: `sqlite3 backend/app.db ".backup backups/app-$(date +%Y%m%d).db"` (daily, 7-day retention)

---

## Key Design Decisions

1. **Dual parser + scoring** over single parser — improves accuracy by ~40%
2. **Anonymous mode** — GuestUser + X-Session-ID header (not cookies) for cross-subdomain session. All features open, no login required. JWT code preserved dormant.
3. **All client components** (`'use client'`) — simple but limits SSR/SEO. OK for tool app.
4. **SQLite as default** — zero-config for small deployments, PostgreSQL for scale. Auto-create tables.
5. **Three-way image merge** — openpyxl + DISPIMG + drawing independently extracted, set-deduped, `||` concatenated.
6. **Per-IP rate limiting** — nginx-aware via X-Forwarded-For
