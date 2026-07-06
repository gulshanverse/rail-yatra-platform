# RailYatra Security Guidelines

This document details the security principles implemented across the **RailYatra** platform.

---

## 🔑 Authentication & Authorization
- **JWT tokens:** Access tokens expire in 15 minutes. Refresh tokens are stored in HttpOnly, SameSite, Secure cookies.
- **Password Hashing:** Implemented using Argon2id.
- **RBAC:** Controllers utilize authorization guards enforcing user scope levels (`GUEST`, `USER`, `PREMIUM`, `ADMIN`, `SUPER_ADMIN`).

---

## 🔒 Network & Threat Mitigation
- **Rate Limiting:** Enforced via NestJS Throttler with sliding Redis count thresholds.
- **Input Sanitization:** DTOs filter out XSS scripts and query parameters prevent SQL injection.
- **Security Headers:** Implements Helmet headers to disable iframe clickjacking and enforce strict HTTPS transport security.
