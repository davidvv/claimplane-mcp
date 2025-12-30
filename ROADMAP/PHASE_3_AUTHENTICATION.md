# Phase 3: Authentication & Authorization System

[← Back to Roadmap](README.md)

---

**Priority**: HIGH - Required before public launch
**Status**: ✅ **COMPLETED** (2025-11-03)
**Estimated Effort**: 2-3 weeks (actual: 1 session)
**Delivered Version**: v0.3.0
**Business Value**: Critical for security and public launch
**📄 Documentation**: See [PHASE3_COMPLETION_PLAN.md](../PHASE3_COMPLETION_PLAN.md)

**Note**: This phase is complete. The checkboxes below represent the original planning requirements and are kept for historical reference.

---

## Overview

Replace the current header-based authentication (`X-Customer-ID`) with a proper JWT-based authentication system with role-based access control.

---

## Features to Implement

### 3.1 User Authentication

**File**: `app/routers/auth.py` (new)

- [ ] `POST /auth/register` - User registration
  - Email validation
  - Password strength requirements
  - Send verification email
  - Create customer record

- [ ] `POST /auth/login` - User login
  - Email/password authentication
  - Return JWT access token + refresh token
  - Track login attempts and lockout after failures

- [ ] `POST /auth/logout` - User logout
  - Invalidate refresh token
  - Add to token blacklist

- [ ] `POST /auth/refresh` - Refresh access token
  - Validate refresh token
  - Issue new access token

- [ ] `POST /auth/forgot-password` - Request password reset
  - Send reset email with token
  - Token expires in 1 hour

- [ ] `POST /auth/reset-password` - Reset password with token
  - Validate token
  - Update password
  - Invalidate all existing tokens

- [ ] `POST /auth/verify-email` - Verify email with token
  - Mark email as verified
  - Enable full account access

- [ ] `POST /auth/resend-verification` - Resend verification email

### 3.2 JWT Token Management

**File**: `app/services/auth_service.py` (new)

- [ ] Generate JWT access tokens (short-lived: 30 min)
- [ ] Generate refresh tokens (long-lived: 7 days)
- [ ] Token validation and parsing
- [ ] Token blacklisting for logout
- [ ] Extract user info from token

**File**: `app/models.py` (update)

Add `User` model (separate from Customer for authentication):

```python
class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)  # Activated after email verification
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="customer")  # customer, admin, reviewer

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to customer profile
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Add `RefreshToken` model:

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add `PasswordResetToken` model:

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.3 Password Security

**File**: `app/services/password_service.py` (new)

- [ ] Hash passwords with bcrypt (passlib already in requirements.txt)
- [ ] Validate password strength
  - Minimum 8 characters
  - At least one uppercase
  - At least one lowercase
  - At least one number
  - At least one special character
- [ ] Check against common password lists
- [ ] Password history (prevent reuse)

### 3.4 Authorization Middleware

**File**: `app/middleware/auth_middleware.py` (new)

- [ ] JWT validation middleware
- [ ] Extract user from token
- [ ] Attach user to request context
- [ ] Handle expired/invalid tokens

**File**: `app/dependencies.py` (new)

- [ ] `get_current_user` dependency - Require valid JWT
- [ ] `get_current_active_user` dependency - Require active user
- [ ] `require_role(role)` dependency factory - Role-based access
- [ ] `require_verified_email` dependency - Email verification check

### 3.5 Role-Based Access Control (RBAC)

Define three roles:

1. **Customer**
   - View own claims
   - Submit new claims
   - Upload documents to own claims
   - View own files

2. **Reviewer**
   - View all claims
   - Update claim status
   - Approve/reject documents
   - Add internal notes

3. **Admin**
   - All reviewer permissions
   - Manage users
   - Access analytics
   - Configure system settings
   - Bulk operations

**File**: `app/services/authorization_service.py` (new)

- [ ] Check if user has permission
- [ ] Check resource ownership
- [ ] Role hierarchy (admin > reviewer > customer)

### 3.6 Update Existing Endpoints

Replace `X-Customer-ID` header with JWT authentication:

- [ ] Update `app/routers/customers.py`
  - Add `current_user` dependency
  - Customers can only access their own data
  - Admins can access all customers

- [ ] Update `app/routers/claims.py`
  - Add `current_user` dependency
  - Customers can only access their own claims
  - Admins/reviewers can access all claims

- [ ] Update `app/routers/files.py`
  - Add `current_user` dependency
  - Verify file ownership on download
  - Admin override for file access

- [ ] Update `app/routers/admin_claims.py` (from Phase 1)
  - Require `reviewer` or `admin` role
  - Track who made changes

### 3.7 Security Features

**File**: `app/services/security_service.py` (new)

- [ ] Rate limiting for login attempts
- [ ] Account lockout after failed attempts
- [ ] Suspicious activity detection
- [ ] Email notifications for security events
  - New login from unknown device
  - Password changed
  - Account locked

**File**: `app/models.py` (update)

Add `LoginAttempt` model for security monitoring:

```python
class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.8 Migration Strategy

**Critical**: Migrate existing customers to the new auth system:

- [ ] Create migration script `scripts/migrate_to_auth.py`
  - Generate `User` record for each existing `Customer`
  - Set temporary password (force reset on first login)
  - Send email with instructions
  - Mark all as unverified initially

- [ ] Maintain backward compatibility temporarily
  - Support both `X-Customer-ID` header and JWT for 2 weeks
  - Add deprecation warnings
  - Track usage to ensure migration is complete

---

## Configuration Updates

**File**: `app/config.py` (update)

```python
# JWT Configuration (already exists, just ensure it's used)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Password Security
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"

# Account Security
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES", "30"))

# Email Verification
EMAIL_VERIFICATION_REQUIRED = os.getenv("EMAIL_VERIFICATION_REQUIRED", "true").lower() == "true"
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS = int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS", "24"))

# Password Reset
PASSWORD_RESET_TOKEN_EXPIRATION_HOURS = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRATION_HOURS", "1"))
```

---

## Testing Requirements

- [ ] Test registration flow
- [ ] Test login with valid/invalid credentials
- [ ] Test token refresh
- [ ] Test password reset flow
- [ ] Test email verification
- [ ] Test account lockout after failed attempts
- [ ] Test role-based access control
- [ ] Test token expiration and renewal
- [ ] Test logout and token invalidation

---

## Success Criteria

- ✅ Users can register and login securely
- ✅ JWT tokens are properly validated
- ✅ Role-based access control is enforced
- ✅ Password reset flow works end-to-end
- ✅ Email verification is required
- ✅ Failed login attempts trigger lockout
- ✅ All existing endpoints use JWT instead of headers
- ✅ Existing customers can migrate to new auth system
- ✅ No regression in existing functionality

---

[← Back to Roadmap](README.md)
