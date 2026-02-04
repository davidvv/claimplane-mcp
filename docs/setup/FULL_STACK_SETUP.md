# Full Stack Setup Guide - ClaimPlane

Complete guide to run the full stack (Backend + Frontend) with Phase 3 JWT authentication.

## Prerequisites

- Python 3.11+ with conda (for backend)
- Node.js 18+ and npm (for frontend)
- PostgreSQL database running
- Redis (for Celery background tasks)

## Backend Setup (FastAPI + PostgreSQL + Redis)

### 1. Activate Conda Environment

```bash
source /Users/david/miniconda3/bin/activate ClaimPlane
```

### 2. Verify Environment Variables

Check `.env` file has:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/claimplane
SECRET_KEY=your-secret-key-here
FILE_ENCRYPTION_KEY=your-fernet-key-here
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Backend Server

```bash
# From project root
python app/main.py
# Or
uvicorn app.main:app --reload
```

Backend will run on: **http://localhost:8000**

API docs available at: **http://localhost:8000/docs**

### 4. Start Celery Worker (Optional - for emails)

In a separate terminal:
```bash
source /Users/david/miniconda3/bin/activate ClaimPlane
celery -A app.celery_app worker --loglevel=info
```

## Frontend Setup (React + Vite)

### 1. Navigate to Frontend Directory

```bash
cd FrontEnd_Claude
```

### 2. Install Dependencies (First time only)

```bash
npm install
```

### 3. Verify Environment Variables

Check `FrontEnd_Claude/.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=
VITE_ANALYTICS_ENABLED=false
```

### 4. Start Frontend Dev Server

```bash
npm run dev
```

Frontend will run on: **http://localhost:3001**

## Testing the Integration

### 1. Registration Flow

1. Open browser to http://localhost:3001
2. Click "Sign Up" tab
3. Fill in registration form:
   - Email: test@example.com
   - Password: TestPassword123! (must meet requirements)
   - First/Last name
4. Click "Create Account"
5. Should see success message and be logged in

### 2. Login Flow

1. Go to http://localhost:3001/auth
2. Use existing account: john.doe@example.com / SecurePassword123!
3. Click "Sign In"
4. Should see welcome message and redirect to home

### 3. Protected Endpoints

After login, the frontend will:
- Store JWT tokens in localStorage
- Automatically add `Authorization: Bearer <token>` to all API requests
- Auto-redirect to /auth if token expires (401 error)

### 4. Test API Calls

Open browser console and check Network tab:
- All API calls should have `Authorization` header
- Claims, files, profile endpoints should work
- No more `X-Customer-ID` or `X-Admin-ID` headers

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (localhost:3001)                  │
│                                                               │
│  React App ──► axios interceptor ──► JWT token from         │
│                                        localStorage           │
│                                                               │
│  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/JSON
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (localhost:8000)                │
│                                                               │
│  JWT Middleware ──► Verify Token ──► Extract User ──►       │
│                                                               │
│  Endpoints:                                                   │
│  • POST /auth/register  (public)                            │
│  • POST /auth/login     (public)                            │
│  • GET  /auth/me        (protected)                         │
│  • GET  /claims/        (protected, ownership verified)     │
│  • POST /claims/        (protected)                         │
│  • GET  /customers/me   (protected)                         │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │   PostgreSQL DB   │
                  │   + Redis Cache   │
                  └───────────────────┘
```

## Key Features Integrated

### Authentication System (Phase 3)

✅ **Registration**
- Form validation (Zod schemas)
- Password requirements (12+ chars, uppercase, lowercase, number, special)
- Bcrypt hashing (12 rounds)
- JWT token generation

✅ **Login**
- Email + password authentication
- Access token (30 min) + refresh token (7 days)
- Device tracking
- Last login timestamp

✅ **Token Management**
- Automatic Bearer token injection
- Token refresh mechanism (future)
- Logout with token revocation
- Auto-redirect on 401 errors

✅ **Authorization**
- Role-based access control (customer/admin/superadmin)
- Ownership verification (IDOR protection)
- Admin-only endpoints
- `/me` endpoints for self-service

### API Integration

✅ **Services Created**
- `src/services/auth.ts` - Authentication API calls
- `src/services/api.ts` - Axios instance with interceptors
- `src/services/claims.ts` - Claims API (ready for JWT)
- `src/services/customers.ts` - Customer API (ready for JWT)
- `src/services/documents.ts` - File uploads (ready for JWT)

✅ **Components Updated**
- `src/pages/Auth.tsx` - Login/Register UI with real backend
- Tab interface (Sign In / Sign Up)
- Form validation matching backend requirements
- Error handling with toast notifications

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
# Restart server
python app/main.py
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
pg_isready
# Recreate tables if needed
python recreate_tables.py
```

**SECRET_KEY errors:**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Update .env file
```

### Frontend Issues

**Module not found errors:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**CORS errors:**
- Backend has CORS enabled for localhost:3001
- Check CORS_ORIGINS in backend config.py

**401 Unauthorized on all requests:**
- Check localStorage has `auth_token`
- Try logging in again
- Check browser console for errors

**Registration fails with "password too weak":**
- Password must be 12+ characters
- Must have uppercase, lowercase, number, special character
- Examples: `TestPassword123!`, `SecurePass#2024`

## Development Workflow

### Making Changes

**Backend Changes:**
```bash
# Code changes auto-reload with uvicorn --reload
# Test endpoints: http://localhost:8000/docs
```

**Frontend Changes:**
```bash
# Vite HMR (Hot Module Replacement) auto-updates
# No need to restart server
```

### Testing End-to-End

1. Register a new user
2. Login with that user
3. Navigate to claim submission
4. Fill out claim form
5. Upload documents
6. Check claim status
7. Verify ownership (can't access other users' claims)

### Admin Testing

1. Create admin user via backend:
```bash
# Use Python console or update user in DB
UPDATE customers SET role = 'admin' WHERE email = 'admin@example.com';
```

2. Login as admin
3. Access admin endpoints
4. Verify admin can see all claims

## Next Steps

After confirming integration works:

1. **Add Email Verification** (Phase 3.1)
   - Confirm email endpoint
   - Email verification flow in UI

2. **Implement Token Refresh** (Phase 3.2)
   - Intercept 401 errors
   - Auto-refresh token before expiry
   - Silent refresh

3. **Add Password Reset UI** (Phase 3.3)
   - "Forgot Password" flow
   - Reset confirmation page

4. **Profile Management** (Phase 3.4)
   - Edit profile page
   - Change password
   - View login history

5. **Admin Dashboard** (Phase 4)
   - Admin UI for claim management
   - File review interface
   - Analytics dashboard

## Security Notes

🔐 **Current Security Status:**
- ✅ JWT authentication with bcrypt passwords
- ✅ HTTPS ready (use in production!)
- ✅ CORS configured
- ✅ Rate limiting framework in place
- ✅ IDOR protection (ownership verification)
- ✅ Input validation on frontend and backend

⚠️ **Before Production:**
- Enable HTTPS/TLS
- Set CORS_ORIGINS to specific domains
- Enable rate limiting
- Add email verification
- Implement MFA (optional)
- Review security audit (docs/SECURITY_AUDIT_v0.2.0.md)

## Support

For issues:
1. Check browser console for frontend errors
2. Check backend logs for API errors
3. Verify both servers are running
4. Test with curl/Postman if UI fails
5. Check this guide's troubleshooting section

---

**Version:** v0.3.0
**Last Updated:** 2025-11-03
**Status:** ✅ Phase 3 Complete - Ready for Integration Testing
