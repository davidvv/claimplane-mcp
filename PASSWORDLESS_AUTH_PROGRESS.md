# Passwordless Authentication Implementation Progress

**Status**: 🟡 In Progress (40% Complete)
**Branch**: UI
**Last Updated**: 2025-11-23
**Next Session Priority**: Complete magic link flow for claim submission emails

---

## 🎯 Goal

Implement fully passwordless authentication using magic links sent via email. Users will never need to create or remember passwords.

### User Flow
1. User submits a claim (no login required)
2. System auto-creates/finds customer account
3. **Email sent with magic link** ("View Your Claim" button)
4. User clicks link → automatically logged in → sees claim details
5. JWT session persists for 7 days (no need to click magic link again)

---

## ✅ Completed (Commits: 20bb456, 2e01569)

### Database & Models
- ✅ Created `MagicLinkToken` model in `app/models.py`
  - Fields: `id`, `user_id`, `claim_id`, `token`, `expires_at`, `created_at`, `used_at`
  - Relationships: Customer ↔ MagicLinkToken ↔ Claim
  - Table created: `magic_link_tokens` with indexes
  - Location: `app/models.py:573-603`

### Backend Services
- ✅ `AuthService.create_magic_link_token()` - `app/services/auth_service.py:509-549`
  - Generates secure 64-byte token using `secrets.token_urlsafe()`
  - Expires after 48 hours
  - Tracks IP address and user agent
  - Returns: `(token_string, MagicLinkToken)`

- ✅ `AuthService.verify_magic_link_token()` - `app/services/auth_service.py:551-594`
  - Validates token (not expired, not used)
  - Marks token as used (sets `used_at`)
  - Updates user's `last_login_at`
  - Returns: `(Customer, claim_id)` or None

### Email Integration
- ✅ Updated `EmailService.send_claim_submitted_email()` - `app/services/email_service.py:113-174`
  - New parameter: `magic_link_token: Optional[str]`
  - Generates magic link URL: `{FRONTEND_URL}/auth/magic-link?token={token}&claim_id={id}`
  - Passes URL to email template

- ✅ Updated `claim_submitted.html` template - `app/templates/emails/claim_submitted.html:83-95`
  - Added "View Your Claim" button (green, centered)
  - Conditional rendering: `{% if magic_link_url %}`
  - Fallback: Copy-pasteable link for email clients without button support

- ✅ Updated Celery task - `app/tasks/claim_tasks.py:40-85`
  - New parameter: `magic_link_token: Optional[str]`
  - Passes token to email service

### Configuration
- ✅ SMTP configured in `.env`
  - Gmail: `idavidvv@gmail.com`
  - App password stored (working, tested)
  - Email notifications enabled

---

## 🔄 In Progress / Not Started

### 🚨 CRITICAL PATH (Must complete for MVP)

#### 1. Update Claims Router (HIGH PRIORITY)
**File**: `app/routers/claims.py`
**Location**: Lines 107-122 (create claim endpoint) and Lines 176-191 (submit claim endpoint)

**What to do**:
```python
# After creating claim, before sending email:

# Import at top
from app.services.auth_service import AuthService
from fastapi import Request

# In both create_claim() and submit_claim_with_customer():
def get_client_info(request: Request):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent

# After claim creation:
ip_address, user_agent = get_client_info(request)

# Create magic link token
magic_token, _ = await AuthService.create_magic_link_token(
    session=session,
    user_id=customer.id,
    claim_id=claim.id,
    ip_address=ip_address,
    user_agent=user_agent
)
await session.commit()  # Important: commit the token!

# Then pass to email task:
send_claim_submitted_email.delay(
    customer_email=customer.email,
    customer_name=f"{customer.first_name} {customer.last_name}",
    claim_id=str(claim.id),
    flight_number=claim.flight_number,
    airline=claim.airline,
    magic_link_token=magic_token  # ← Add this
)
```

**Files to modify**:
- `app/routers/claims.py` (2 endpoints)

---

#### 2. Create Magic Link Verification Endpoint (HIGH PRIORITY)
**File**: `app/routers/auth.py`
**Where**: Add after line 297 (after logout endpoint)

**What to do**:
```python
@router.post(
    "/magic-link/verify/{token}",
    response_model=AuthResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Verify magic link token",
    description="Verify a magic link token and return JWT tokens for authentication."
)
async def verify_magic_link(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Verify magic link token and authenticate user.

    Args:
        token: Magic link token from email URL
        request: FastAPI request object
        session: Database session

    Returns:
        AuthResponseSchema with user info and JWT tokens

    Raises:
        HTTPException: 400 if token is invalid or expired
    """
    # Get client info
    ip_address, user_agent = get_client_info(request)

    # Verify token
    result = await AuthService.verify_magic_link_token(
        session=session,
        token=token
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link token"
        )

    customer, claim_id = result

    # Generate JWT tokens
    access_token = AuthService.create_access_token(
        user_id=customer.id,
        email=customer.email,
        role=customer.role
    )

    refresh_token_str, _ = await AuthService.create_refresh_token(
        session=session,
        user_id=customer.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    await session.commit()

    # Return auth response
    return AuthResponseSchema(
        user=UserResponseSchema.model_validate(customer),
        tokens=TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="Bearer",
            expires_in=config.JWT_EXPIRATION_MINUTES * 60
        )
    )
```

**Schema needed** (already exists in `app/schemas/auth_schemas.py`):
- ✅ `AuthResponseSchema`
- ✅ `UserResponseSchema`
- ✅ `TokenResponseSchema`

---

#### 3. Create Frontend Magic Link Handler (HIGH PRIORITY)
**File**: Create `frontend_Claude45/src/pages/Auth/MagicLinkPage.tsx`

**What to do**:
```typescript
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '@/services/api';

export function MagicLinkPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get('token');
      const claimId = searchParams.get('claim_id');

      if (!token) {
        setStatus('error');
        setErrorMessage('No token provided');
        return;
      }

      try {
        // Verify magic link token
        const response = await apiClient.post(`/auth/magic-link/verify/${token}`);

        // Store tokens
        localStorage.setItem('auth_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        localStorage.setItem('user_email', response.data.user.email);
        localStorage.setItem('user_id', response.data.user.id);
        localStorage.setItem('user_name', `${response.data.user.first_name} ${response.data.user.last_name}`);

        setStatus('success');

        // Redirect to claim page or dashboard
        setTimeout(() => {
          if (claimId) {
            navigate(`/claims/${claimId}`);
          } else {
            navigate('/dashboard');
          }
        }, 1500);

      } catch (error: any) {
        console.error('Magic link verification failed:', error);
        setStatus('error');
        setErrorMessage(error.response?.data?.detail || 'Invalid or expired link');
      }
    };

    verifyToken();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        {status === 'verifying' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <h2 className="mt-6 text-xl font-semibold">Verifying your link...</h2>
            <p className="mt-2 text-muted-foreground">Please wait a moment</p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-green-600">Success!</h2>
            <p className="mt-2 text-muted-foreground">Redirecting you to your claim...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="text-6xl mb-4">✕</div>
            <h2 className="text-2xl font-bold text-red-600">Link Invalid</h2>
            <p className="mt-2 text-muted-foreground">{errorMessage}</p>
            <p className="mt-4 text-sm">
              Magic links expire after 48 hours. Please request a new one.
            </p>
            <button
              onClick={() => navigate('/')}
              className="mt-6 px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
            >
              Go to Home
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Then add route** in `frontend_Claude45/src/App.tsx`:
```typescript
import { MagicLinkPage } from '@/pages/Auth/MagicLinkPage';

// In routes array:
<Route path="/auth/magic-link" element={<MagicLinkPage />} />
```

---

## 🔮 Future Work (Not Required for MVP)

### Phase 2: Full Passwordless Migration
- Remove password fields from LoginPage
- Remove password-based registration
- Add "Request Magic Link" endpoint for returning users
- Create generic `magic_link.html` email template
- Update frontend to be fully passwordless

### Phase 3: Enhanced UX
- Add "Resend Magic Link" functionality
- Add magic link expiration countdown in emails
- Add branded email templates with logo
- Add magic link usage analytics

---

## 🧪 Testing Checklist

Once above 3 items are complete, test this flow:

1. **Submit a claim** (use test email `idavidvv+AEC@gmail.com`)
   - Go to http://localhost:3000/claim
   - Fill out claim form
   - Submit

2. **Check email**
   - Should receive "Claim Submitted" email
   - Should see green "View Your Claim" button
   - URL format: `http://localhost:3000/auth/magic-link?token=...&claim_id=...`

3. **Click magic link**
   - Should see "Verifying your link..." spinner
   - Should see "Success!" message
   - Should auto-redirect to claim details page
   - Should be logged in (check localStorage for tokens)

4. **Verify session persistence**
   - Close browser
   - Reopen and go to dashboard
   - Should still be logged in (JWT refresh token)

5. **Test token expiration**
   - Wait 48 hours (or manually expire token in DB)
   - Try to use link
   - Should see "Invalid or expired link" error

---

## 📁 Key Files Reference

### Backend
- **Models**: `app/models.py` (lines 573-603)
- **Auth Service**: `app/services/auth_service.py` (lines 509-594)
- **Email Service**: `app/services/email_service.py` (lines 113-174)
- **Celery Tasks**: `app/tasks/claim_tasks.py` (lines 40-85)
- **Claims Router**: `app/routers/claims.py` ⚠️ NEEDS UPDATE
- **Auth Router**: `app/routers/auth.py` ⚠️ NEEDS NEW ENDPOINT

### Frontend
- **Magic Link Handler**: ⚠️ NEEDS CREATION `frontend_Claude45/src/pages/Auth/MagicLinkPage.tsx`
- **App Routes**: `frontend_Claude45/src/App.tsx` ⚠️ NEEDS NEW ROUTE

### Email Templates
- **Claim Submitted**: `app/templates/emails/claim_submitted.html` (lines 83-95)

### Configuration
- **Environment**: `.env` (lines 57-65)

---

## 🐛 Known Issues / Gotchas

1. **Celery worker must be restarted** after code changes to backend
   - Run: `celery -A app.celery_app worker --loglevel=info`

2. **Frontend URL configuration**
   - Add to `.env`: `FRONTEND_URL=http://localhost:3000`
   - Currently defaults to `http://localhost:3000`

3. **Magic link tokens are single-use**
   - After clicking once, token is marked as `used_at`
   - Second click will fail with "Invalid or expired" error
   - This is intentional for security

4. **Session management**
   - JWT access token: 30 minutes
   - JWT refresh token: 7 days
   - Magic link token: 48 hours

---

## 💡 Quick Start for Next Session

```bash
# 1. Activate environment
source /Users/david/miniconda3/bin/activate EasyAirClaim

# 2. Start services (in separate terminals)
# Terminal 1: PostgreSQL & Redis
docker-compose up -d db redis

# Terminal 2: Backend
python -m uvicorn app.main:app --reload

# Terminal 3: Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 4: Frontend
cd frontend_Claude45 && npm run dev

# 3. Implement the 3 critical items above

# 4. Test the flow

# 5. Commit and push
git add .
git commit -m "feat(auth): complete passwordless magic link authentication"
git push origin UI
```

---

## 📊 Progress Tracking

- [x] Database model (MagicLinkToken)
- [x] Auth service methods (create/verify tokens)
- [x] Email service integration
- [x] Email template with button
- [x] Celery task updates
- [ ] Claims router magic link generation ⚠️ **NEXT**
- [ ] Magic link verification endpoint ⚠️ **NEXT**
- [ ] Frontend magic link handler ⚠️ **NEXT**
- [ ] End-to-end testing
- [ ] Remove password-based auth (future)

**Estimated Time to Complete MVP**: 1-1.5 hours

---

## 🤝 Questions?

If anything is unclear, check:
1. This document first
2. Git commit messages: `git log --oneline`
3. Code comments in the files above
4. CLAUDE.md for project structure

Good luck! 🚀
