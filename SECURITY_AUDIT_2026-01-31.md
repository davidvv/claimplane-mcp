# Security Audit Report - January 31, 2026

## 1. Executive Summary
A comprehensive security audit of the ClaimPlane application has been performed. The application demonstrates strong security foundations, including robust authentication (JWT with HTTP-only cookies), data validation (Pydantic), and proactive file security (encryption, virus scanning).

However, several critical and high-priority issues were identified, most notably a **broken streaming encryption implementation** for large files and **exposed infrastructure components** (Redis without password).

## 2. Findings & Risk Assessment

| ID | Title | Severity | Category | Status |
|----|-------|----------|----------|--------|
| S-01 | Broken Streaming Encryption | **CRITICAL** | Data Integrity | Open |
| S-02 | Redis Exposed Without Password | **HIGH** | Infrastructure | Open |
| S-03 | Docker Socket Mounting in Webhook | **HIGH** | Infrastructure | Open |
| S-04 | Duplicate Cookie Headers | **MEDIUM** | Auth | Open |
| S-05 | MIME Type Spoofing Fallback | **MEDIUM** | File Security | Open |
| S-06 | Fail-Open Virus Scanning | **MEDIUM** | File Security | Open |
| S-07 | PII Disclosure in OCR Logs | **LOW** | Privacy | Open |
| S-08 | Redundant Security Headers | **LOW** | API Security | Open |

---

## 3. Detailed Findings

### S-01: Broken Streaming Encryption (CRITICAL)
- **Description**: `EncryptionService.encrypt_chunk` uses Fernet's `encrypt()` on individual chunks. Fernet is a message-based encryption scheme that adds metadata (salt, IV, HMAC) to every call. Concatenating these results in a file that cannot be decrypted as a single stream.
- **Impact**: All files larger than 50MB (streaming threshold) are corrupted upon upload and cannot be downloaded/decrypted.
- **Remediation**: Implement a proper streaming encryption mode (e.g., AES-GCM or AES-CTR) or use Fernet only for small files and a different strategy for large files.

### S-02: Redis Exposed Without Password (HIGH)
- **Description**: The `redis` service in `docker-compose.yml` exposes port 6379 to the host without any authentication.
- **Impact**: If the host is accessible from the internet or a compromised internal network, anyone can access the Redis store, read session data, or manipulate task queues.
- **Remediation**: Remove the port exposure if not needed externally, or add `requirepass` to Redis configuration.

### S-03: Docker Socket Mounting in Webhook (HIGH)
- **Description**: The `webhook` service mounts `/var/run/docker.sock`.
- **Impact**: A vulnerability in the webhook service allows an attacker to gain full control over the host system.
- **Remediation**: Use a dedicated deployment runner or a more restricted API for Docker management if possible. Ensure the `WEBHOOK_SECRET` is extremely strong.

### S-04: Duplicate Cookie Headers (MEDIUM)
- **Description**: `AuthService.set_auth_cookies` sets the `refresh_token` cookie twice with different `SameSite` values (`Strict` and `Lax`).
- **Impact**: Undefined browser behavior; typically the last header wins, which might accidentally lower security from `Strict` to `Lax`.
- **Remediation**: Remove the duplicate `set_cookie` call and stick to `Strict` for best security.

### S-05: MIME Type Spoofing Fallback (MEDIUM)
- **Description**: `FileValidationService._detect_mime_type` falls back to `mimetypes.guess_type(filename)` if `libmagic` fails.
- **Impact**: An attacker can bypass MIME type restrictions by providing a fake extension (e.g., `malicious.exe` renamed to `malicious.pdf`).
- **Remediation**: Only trust content-based detection (`libmagic`). If it fails, reject the file or treat it as `application/octet-stream` with strict handling.

### S-06: Fail-Open Virus Scanning (MEDIUM)
- **Description**: If the ClamAV service is down, `FileValidationService` logs a warning but allows the upload to proceed.
- **Impact**: Malware can be uploaded if the security service is temporarily unavailable.
- **Remediation**: Change to a "fail-closed" policy for production.

### S-07: PII Disclosure in OCR Logs (LOW)
- **Description**: `OCRService` logs samples of extracted data and full Gemini responses.
- **Impact**: Names, booking references, and other PII are stored in application logs.
- **Remediation**: Sanitize logs before printing or use a lower log level (DEBUG) that is disabled in production.

### S-08: Redundant Security Headers (LOW)
- **Description**: Headers like `X-Frame-Options` and `X-Content-Type-Options` are added in both `app/main.py` and `FileSecurityMiddleware`.
- **Impact**: Larger response size, potential browser confusion.
- **Remediation**: Centralize header management in one middleware.

## 4. Remediation Plan

1.  **Immediate Fix (S-01)**: Fix the `EncryptionService` to support proper chunking or disable streaming until fixed.
2.  **Infrastructure Hardening (S-02, S-03)**: Secure Redis and review webhook permissions.
3.  **Auth Cleanup (S-04)**: Fix the duplicate cookie issue.
4.  **File Security (S-05, S-06)**: Tighten MIME detection and virus scan policies.
5.  **Logging & Headers (S-07, S-08)**: Sanitize OCR logs and deduplicate middleware headers.
