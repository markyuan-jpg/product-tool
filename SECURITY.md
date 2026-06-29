# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please email:
**support@quoteflow.it.com**

Do NOT open a public issue. We will respond within 48 hours.

## Scope

This policy covers:
- `quoteflow.it.com` (frontend)
- `api.quoteflow.it.com` (backend API)
- `product_tool/` (parsing engine)
- All deployed infrastructure

## Security Measures

### Authentication
- Primary: Anonymous mode — GuestUser + X-Session-ID header (no password required)
- Dormant: JWT access tokens (15 min) + refresh tokens (7 days, httpOnly cookie)
- Dormant: bcrypt password hashing (never stored in plaintext)

### Rate Limiting
- Login/Register: 5 requests/minute/IP
- Forgot Password: 3 requests/minute/IP
- File Parse: 20 requests/minute/IP

### Data Protection
- Input sanitization: HTML escaping on all stored text fields
- File size limit: 50MB max upload
- File extension whitelist: `.xlsx`, `.xls`, `.pdf`, `.docx` only
- Original uploaded files: deleted after processing

### Transport Security
- HTTPS enforced (SSL via Let's Encrypt)
- HSTS: `max-age=63072000; includeSubDomains; preload`
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- CORS: strict origin whitelist

### Infrastructure
- Database: SQLAlchemy ORM (parameterized queries — SQL injection resistant)
- Backend: regular dependency updates
- Error monitoring: Sentry (production)
- Cookie security: httpOnly, Secure, SameSite=None, domain=.quoteflow.it.com (cross-subdomain session)

## Known Limitations

- No CAPTCHA on registration (registered users can brute-force usernames)
- No Web Application Firewall (WAF) in front of the API
- Password minimum length: 6 characters (low — will be increased)
- No email verification on signup
- No 2FA option

## Responsible Disclosure

We follow a 90-day disclosure policy:
1. Report received → acknowledgment within 48 hours
2. Fix developed → within 30 days (critical) or 90 days (standard)
3. Credit given in release notes (unless reporter prefers anonymity)
