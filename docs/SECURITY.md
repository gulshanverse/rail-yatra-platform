# RailYatra Production Security Hardening Guidelines

This document details rate-limiting configurations, CORS controls, and security headers applied to protect RailYatra.

---

## 1. Rate Limiting Limits
We enforce an active rate limiter middleware under `SecurityAndRateLimitMiddleware`:
- **Limit**: 150 requests per IP address per 1 minute window.
- **Headers**: Returns `Retry-After` header specifying the block period in seconds.
- **Fail response**: Returns `429 Too Many Requests`.

---

## 2. Security Headers (Secure Defaults)
We inject standard headers on all incoming requests to mitigate common vulnerabilities:
- `X-Content-Type-Options: nosniff`: Prevents MIME-sniffing.
- `X-Frame-Options: DENY`: Mitigates clickjacking attacks.
- `X-XSS-Protection: 1; mode=block`: Blocks XSS execution.
- `Content-Security-Policy`: Restricts script and stylesheet execution origins.
- `Strict-Transport-Security`: Forces browser HTTP to HTTPS redirections.
- `Referrer-Policy: strict-origin-when-cross-origin`: Minimizes metadata exposure.
