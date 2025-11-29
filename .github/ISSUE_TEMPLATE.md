# Issue: Implement Passwordless Magic Link Authentication

## Problem
Currently using temporary password-based auto-registration which is not ideal for user experience.

## Proposed Solution
Implement passwordless authentication using magic links sent via email:

### Backend Changes
1. **Create `/auth/magic-link/request` endpoint**
   - Accept email address
   - Generate secure token (JWT or random secure token)
   - Store token in database with expiration (15 minutes)
   - Send email with magic link

2. **Create `/auth/magic-link/verify` endpoint**
   - Accept token from URL
   - Validate token (not expired, not used)
   - Create session and return JWT tokens
   - Mark token as used

3. **Update claim submission flow**
   - Remove password requirement from auto-registration
   - Automatically send magic link after claim submission
   - User clicks link to access their account

### Frontend Changes
1. Update auth service to support magic link flow
2. Add magic link request page
3. Add magic link verification handler
4. Update success page to mention magic link email

### Benefits
- ✅ Better UX - no passwords to remember
- ✅ More secure - tokens expire quickly
- ✅ Faster onboarding - one-click authentication
- ✅ Mobile-friendly - works on any device

### Technical Details
- **Token storage**: `magic_link_tokens` table
- **Token format**: Secure random string (32 bytes)
- **Expiration**: 15 minutes
- **Email template**: Include branded magic link button
- **Rate limiting**: Max 3 requests per email per hour

### Database Schema
```sql
CREATE TABLE magic_link_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL
);

CREATE INDEX idx_magic_link_token ON magic_link_tokens(token);
CREATE INDEX idx_magic_link_email ON magic_link_tokens(email);
```

### Related Files
- Backend: `app/routers/auth.py`, `app/services/auth_service.py`
- Frontend: `src/services/auth.ts`, `src/pages/Auth.tsx`
- Email: `app/services/email_service.py`

### Priority
**High** - Current workaround uses temporary passwords which is suboptimal

### Labels
- `enhancement`
- `authentication`
- `security`
- `user-experience`

---

**Created**: 2025-11-06
**Status**: Planned
**Assignee**: TBD
