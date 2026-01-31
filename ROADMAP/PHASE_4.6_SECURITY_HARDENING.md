# Phase 4.6: Post-Audit Security & Privacy Hardening

[← Back to Roadmap](README.md)

---

**Priority**: CRITICAL - Addressing findings from Jan 31, 2026 Security Audit
**Status**: ⏳ **IN PROGRESS** (2026-01-31)
**Business Value**: GDPR compliance, Brute-force protection, Data-at-Rest security
**Scope**: Remediation of P0/P1 risks identified in `SECURITY_AUDIT_2026-01-31.md`

---

### Overview
Following a comprehensive security and privacy audit, several critical and high-priority vulnerabilities were identified. This phase focuses on closing these gaps to ensure the application is robust against targeted attacks and fully compliant with privacy regulations.

### 🚨 CRITICAL (P0) - Must Fix Immediately

#### 4.6.1 Redis Exposure Hardening
**Risk**: Unauthorized access to session data and background tasks via exposed port 6379.
**Status**: ✅ **FIXED** (2026-01-31)
**Tasks**:
- [x] Remove external port binding in `docker-compose.yml`
- [x] Implement `requirepass` authentication for Redis
- [x] Update connection strings in API and Celery workers

#### 4.6.2 Encrypt PII at Rest
**Risk**: Data leakage in case of database compromise (SQLi or backup theft).
**Status**: ✅ **FIXED** (2026-01-31)
**Strategy**: Hybrid Approach (Deterministic Blind Indexing + Encrypted Storage)
**Tasks**:
- [x] Add `sqlalchemy-utils` and `cryptography` dependencies
- [x] Define `DB_ENCRYPTION_KEY` configuration
- [x] Implement `EncryptedType` for PII fields (Name, Email, Phone, Address)
- [x] Implement Blind Indexing for searchability (Exact Match)
- [x] Migrate existing plain-text data

### ⚠️ HIGH PRIORITY (P1) - Fix for Next Release

#### 4.6.3 Account Lockout Strategy
**Risk**: Distributed brute-force attacks against user accounts.
**Status**: ✅ **FIXED** (2026-01-31)
**Tasks**:
- [x] Add `failed_login_attempts` and `locked_until` to Customer model
- [x] Implement Redis-based high-speed tracking
- [x] Implement Exponential Backoff (5s -> 30s -> 60s)
- [x] Implement 24-hour lockout after 10 failed attempts

#### 4.6.4 Strict MIME Type Validation
**Risk**: File upload attacks (e.g., polyglots, masked executables).
**Status**: ✅ **FIXED** (2026-01-31)
**Tasks**:
- [x] Enforce `libmagic` content-based detection
- [x] Remove insecure file extension fallback
- [x] Implement "Peek-and-Seek" validation for large file streams

#### 4.6.5 GDPR Deep Anonymization
**Risk**: "Right to Erasure" not fully removing PII (Passengers, PNRs).
**Status**: ✅ **FIXED** (2026-01-31)
**Tasks**:
- [x] Scrub linked Passenger records
- [x] Nullify high-entropy identifiers (PNR, Ticket Number)
- [x] Scrub Claim Notes and Audit Logs (IP addresses)
- [x] Physically delete authentication tokens

### 📋 MEDIUM PRIORITY (P2) - Technical Debt

#### 4.6.6 Redact PII from Logs
**Risk**: Sensitive data leakage into application logs.
**Status**: 📅 **BACKLOG**
**Tasks**:
- [ ] Sanitize OCR logs
- [ ] Redact PII from request/response logging

---

### ✅ Post-Verification Fixes (Added 2026-01-31)
#### 4.6.7 Wizard Step 4 Regression Fix
**Issue**: "Sign & Continue" button was unresponsive due to localStorage clearing and missing backend endpoint.
**Status**: ✅ **FIXED & VERIFIED**
**Tasks**:
- [x] Fix aggressive localStorage clearing in `getStoredUserInfo`
- [x] Restore lost `sign-poa` endpoint and clean up router duplicates
- [x] Implement robust `draftClaimId` persistence in `ClaimFormPage`
- [x] E2E Verification with `agent-browser` (Reached Step 5)

#### 4.6.8 Optional Documents & Upload Reliability
**Issue**: Customers were forced to upload documents or provide PNR, even when not strictly required. Persistence issues caused false "upload failed" errors.
**Status**: ✅ **FIXED** (2026-01-31)
**Tasks**:
- [x] Make Booking Reference and Documents optional in Step 3
- [x] Fix Step 5 logic to ignore already-uploaded documents
- [x] Synchronize draft state with persistence hook to prevent loss after refresh

---

### Timeline
- **Start Date**: 2026-01-31
- **Target Completion**: 2026-02-01
