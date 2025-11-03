# Phase 3 - Authentication & Authorization System

**Target Version**: v0.3.0
**Status**: 📋 **PLANNED** (Not started)
**Priority**: CRITICAL for public launch
**Estimated Effort**: 2-3 weeks (or 1-2 focused sessions)
**Business Value**: ESSENTIAL - Security foundation for production

---

## Overview

Replace insecure header-based authentication (`X-Customer-ID`, `X-Admin-ID`) with a robust JWT-based authentication system with role-based access control (RBAC). This is **required before public launch** and enables proper multi-user support.

---

## 🎯 Goals

1. **Secure Authentication**: JWT tokens instead of header IDs
2. **User Management**: Registration, login, password reset
3. **Role-Based Access**: Customers vs Admins with different permissions
4. **Token Lifecycle**: Access tokens, refresh tokens, revocation
5. **Security Hardening**: Password hashing, rate limiting, audit logging

---

## 📋 Features to Implement

### 3.1 Database Models

**File**: `app/models.py` (update)

Add three new models:

#### User Model
```python
class User(Base):
    """User account (customers and admins)"""
    __tablename__ = "users"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)

    # Role & Status
    role = Column(String(20), nullable=False, default="customer")  # customer, admin, superadmin
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True, unique=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    # Link to existing Customer model (optional - for migration)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=True, unique=True)
    customer = relationship("Customer", back_populates="user")
```

#### RefreshToken Model
```python
class RefreshToken(Base):
    """Refresh tokens for JWT rotation"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Device tracking
    device_info = Column(String(255), nullable=True)  # User-Agent
    ip_address = Column(String(45), nullable=True)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self):
        return not self.revoked_at and self.expires_at > datetime.utcnow()
```

#### PasswordResetToken Model
```python
class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)  # 1 hour expiry
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="password_resets")

    @property
    def is_valid(self):
        return not self.used_at and self.expires_at > datetime.utcnow()
```

### 3.2 Services

#### PasswordService
**File**: `app/services/password_service.py` (new)

```python
class PasswordService:
    """Password hashing and validation using bcrypt"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt (cost factor 12)"""
        # Use bcrypt with salt rounds = 12
        pass

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        pass

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate password meets requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number
        - At least 1 special character

        Returns (is_valid, list_of_errors)
        """
        pass
```

#### AuthService
**File**: `app/services/auth_service.py` (new)

```python
class AuthService:
    """JWT token management and authentication logic"""

    @staticmethod
    def create_access_token(user_id: UUID, role: str) -> str:
        """
        Create JWT access token
        - Expiry: 15 minutes
        - Claims: user_id, role, issued_at, expires_at
        """
        pass

    @staticmethod
    def create_refresh_token(user_id: UUID) -> tuple[str, str]:
        """
        Create refresh token
        - Returns: (token, token_hash)
        - Expiry: 7 days
        - Store hash in database
        """
        pass

    @staticmethod
    def verify_access_token(token: str) -> dict:
        """
        Verify and decode JWT access token
        Returns payload if valid, raises exception if invalid/expired
        """
        pass

    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
        session: AsyncSession
    ) -> tuple[str, str]:
        """
        Exchange refresh token for new access + refresh tokens
        - Invalidate old refresh token (rotation)
        - Create new refresh token
        - Return (new_access_token, new_refresh_token)
        """
        pass

    @staticmethod
    async def revoke_refresh_token(token_hash: str, session: AsyncSession):
        """Revoke a refresh token"""
        pass

    @staticmethod
    def create_email_verification_token() -> str:
        """Create secure random token for email verification"""
        pass

    @staticmethod
    def create_password_reset_token() -> str:
        """Create secure random token for password reset"""
        pass
```

### 3.3 Authentication Middleware

**File**: `app/middleware/jwt_middleware.py` (new)

```python
class JWTAuthMiddleware:
    """FastAPI dependency for JWT authentication"""

    async def __call__(
        self,
        request: Request,
        authorization: str = Header(None)
    ) -> dict:
        """
        Extract and validate JWT from Authorization header
        Format: "Bearer <token>"

        Returns user payload: {user_id, role}
        Raises HTTPException 401 if invalid
        """
        pass

# Helper dependencies
async def get_current_user(
    token_data: dict = Depends(JWTAuthMiddleware()),
    session: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    pass

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(403, "Admin access required")
    return current_user

async def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Require superadmin role"""
    if current_user.role != "superadmin":
        raise HTTPException(403, "Superadmin access required")
    return current_user
```

### 3.4 Authentication Endpoints

**File**: `app/routers/auth.py` (new)

```python
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(
    registration: UserRegistrationRequest,
    session: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register new user account
    - Validate email uniqueness
    - Validate password strength
    - Hash password
    - Create user record
    - Send email verification email
    - Return user data (without password)
    """
    pass

@router.post("/login")
async def login(
    credentials: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Login with email and password
    - Verify email exists
    - Check account not locked
    - Verify password
    - Create access + refresh tokens
    - Update last_login_at and failed_login_attempts
    - Return tokens + user info
    """
    pass

@router.post("/refresh")
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using refresh token
    - Verify refresh token is valid and not revoked
    - Create new access token
    - Rotate refresh token (invalidate old, create new)
    - Return new tokens
    """
    pass

@router.post("/logout")
async def logout(
    refresh_token: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Logout user
    - Revoke refresh token
    - Return success message
    """
    pass

@router.post("/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Verify email address using token
    - Find user by verification token
    - Check token not expired
    - Set is_email_verified = True
    - Clear verification token
    """
    pass

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Request password reset
    - Find user by email
    - Create password reset token (1 hour expiry)
    - Send password reset email
    - Return success (don't reveal if email exists)
    """
    pass

@router.post("/reset-password")
async def reset_password(
    reset_request: PasswordResetRequest,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Reset password using token
    - Verify token is valid and not used
    - Validate new password strength
    - Hash new password
    - Update user password
    - Mark token as used
    - Revoke all refresh tokens (force re-login)
    """
    pass

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user info"""
    pass

@router.put("/me")
async def update_current_user(
    update_request: UserUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Update current user profile"""
    pass

@router.put("/me/password")
async def change_password(
    password_change: PasswordChangeRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Change password (requires current password)
    - Verify current password
    - Validate new password
    - Update password
    - Revoke all refresh tokens (force re-login everywhere)
    """
    pass
```

### 3.5 Admin User Management

**File**: `app/routers/admin_users.py` (new)

```python
router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

@router.get("")
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> PaginatedUsersResponse:
    """List all users with filtering"""
    pass

@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserDetailResponse:
    """Get user details"""
    pass

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin)
) -> UserResponse:
    """Update user role (superadmin only)"""
    pass

@router.put("/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    status_update: UserStatusUpdateRequest,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> UserResponse:
    """
    Activate/deactivate user account
    - Set is_active flag
    - If deactivating, revoke all refresh tokens
    """
    pass

@router.delete("/{user_id}/sessions")
async def revoke_user_sessions(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    """Revoke all user sessions (force logout)"""
    pass
```

### 3.6 Protected Endpoints Migration

Update all existing endpoints to use JWT authentication:

#### Customer Endpoints
```python
# Before:
def get_customer_id(request: Request) -> UUID:
    customer_id = request.headers.get("X-Customer-ID")
    ...

# After:
@router.get("/claims")
async def get_my_claims(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # current_user.id is the authenticated user
    # current_user.customer_id links to Customer record
    ...
```

#### Admin Endpoints
```python
# Before:
def get_admin_user_id(request: Request) -> UUID:
    admin_id = request.headers.get("X-Admin-ID")
    ...

# After:
@router.put("/admin/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: UUID,
    update_request: ClaimStatusUpdateRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    # admin.id is the authenticated admin user
    ...
```

### 3.7 Schemas

**File**: `app/schemas/auth_schemas.py` (new)

```python
# Registration
class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    phone: Optional[str] = None

# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

# Token refresh
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Password reset
class PasswordResetRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=100)

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)

# User response
class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# User update
class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

# Admin schemas
class UserRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(customer|admin|superadmin)$")

class UserStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None
```

### 3.8 Security Configuration

**File**: `app/config.py` (update)

```python
# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-THIS-IN-PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True

# Account Security
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION_MINUTES = 30

# Email Verification
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1
```

### 3.9 Email Templates

**Directory**: `app/templates/emails/` (update)

Add 3 new email templates:

1. **email_verification.html**
   - Welcome message
   - Verification link with token
   - Link expiry time (24 hours)

2. **password_reset.html**
   - Password reset link
   - Token expiry time (1 hour)
   - Security notice

3. **password_changed.html**
   - Confirmation that password was changed
   - If not you, contact support

### 3.10 Dependencies

**File**: `requirements.txt` (update)

```txt
# Authentication
python-jose[cryptography]==3.3.0  # JWT token encoding/decoding
passlib[bcrypt]==1.7.4  # Password hashing
python-multipart==0.0.6  # For form data parsing
```

---

## 🔄 Migration Strategy

### Phase 1: Add New Models (Non-Breaking)
1. Create User, RefreshToken, PasswordResetToken models
2. Run Alembic migration
3. Add optional `user_id` foreign key to Customer model
4. Existing endpoints continue using header-based auth

### Phase 2: Create Migration Script
1. Script to create User records from existing Customer records
2. Link Customer.user_id to User.id
3. Set default password (require password reset on first login)

### Phase 3: Implement New Endpoints
1. Create all `/auth` endpoints
2. Test thoroughly with Postman/pytest
3. Existing endpoints still work with headers

### Phase 4: Migrate Endpoints (Breaking Change)
1. Update all customer endpoints to use `Depends(get_current_user)`
2. Update all admin endpoints to use `Depends(require_admin)`
3. Remove header-based authentication helpers
4. Update frontend to use JWT tokens
5. **BREAKING CHANGE**: Old header-based auth stops working

### Phase 5: Cleanup
1. Remove X-Customer-ID and X-Admin-ID dependencies
2. Update documentation
3. Update tests
4. Deploy to production

---

## 🧪 Testing Strategy

### Unit Tests
- Password hashing/verification
- Token creation/validation
- Password strength validation
- Token expiry handling

### Integration Tests
- Registration flow
- Login flow
- Token refresh flow
- Password reset flow
- Email verification flow
- Protected endpoint access
- Role-based access control

### Security Tests
- Invalid token handling
- Expired token handling
- Revoked token handling
- SQL injection attempts
- Brute force protection
- Password reset token reuse
- CORS configuration

### Load Tests
- Concurrent login requests
- Token refresh under load
- Database connection pooling

---

## 📊 Success Criteria

- ✅ All endpoints use JWT authentication
- ✅ No more header-based auth
- ✅ User registration working
- ✅ Login/logout working
- ✅ Password reset working
- ✅ Email verification working
- ✅ Token refresh working
- ✅ Role-based access control working
- ✅ Account lockout working (brute force protection)
- ✅ All existing tests passing
- ✅ New authentication tests passing (>90% coverage)
- ✅ Security audit passed
- ✅ Documentation updated

---

## 🚨 Security Considerations

### Critical Security Measures

1. **Password Storage**
   - Never store plain text passwords
   - Use bcrypt with cost factor 12+
   - Implement password strength requirements

2. **Token Security**
   - Use secure random tokens for reset/verification
   - Short-lived access tokens (15 minutes)
   - Refresh token rotation
   - Store only token hashes in database

3. **Rate Limiting**
   - Limit login attempts per IP
   - Limit password reset requests per email
   - Account lockout after failed attempts

4. **Email Security**
   - Use secure tokens (not user ID)
   - Time-limited tokens
   - Single-use tokens

5. **Session Management**
   - Track device/IP for suspicious activity
   - Allow users to view/revoke active sessions
   - Revoke all sessions on password change

6. **HTTPS Only**
   - JWT tokens only transmitted over HTTPS
   - Secure cookie flags
   - HSTS headers

---

## 📝 Implementation Checklist

### Preparation
- [ ] Read security best practices for JWT authentication
- [ ] Review OWASP authentication guidelines
- [ ] Plan database migration strategy
- [ ] Set up test user accounts

### Database
- [ ] Create User model
- [ ] Create RefreshToken model
- [ ] Create PasswordResetToken model
- [ ] Create Alembic migration
- [ ] Test migration on dev database

### Services
- [ ] Implement PasswordService
- [ ] Implement AuthService
- [ ] Write unit tests for services

### Middleware
- [ ] Implement JWTAuthMiddleware
- [ ] Create dependency helpers (get_current_user, require_admin)
- [ ] Test middleware with various token scenarios

### Endpoints
- [ ] Create /auth router
- [ ] Implement registration endpoint
- [ ] Implement login endpoint
- [ ] Implement refresh endpoint
- [ ] Implement logout endpoint
- [ ] Implement password reset endpoints
- [ ] Implement email verification endpoint
- [ ] Test all endpoints with Postman

### Email Templates
- [ ] Create email verification template
- [ ] Create password reset template
- [ ] Create password changed template
- [ ] Test email rendering

### Migration
- [ ] Update customer endpoints to use JWT
- [ ] Update admin endpoints to use JWT
- [ ] Remove header-based auth
- [ ] Update tests
- [ ] Update API documentation

### Admin Features
- [ ] Create admin/users router
- [ ] Implement user management endpoints
- [ ] Test admin functionality

### Testing
- [ ] Write authentication integration tests
- [ ] Write authorization tests
- [ ] Write security tests
- [ ] Load testing
- [ ] Security audit

### Documentation
- [ ] Update API documentation
- [ ] Update deployment guide
- [ ] Create migration guide
- [ ] Update CLAUDE.md

### Deployment
- [ ] Deploy to staging
- [ ] Run full test suite
- [ ] Security review
- [ ] Deploy to production
- [ ] Monitor for issues

---

## 📚 Resources

### Libraries
- **python-jose**: JWT token handling
- **passlib**: Password hashing (bcrypt)
- **python-multipart**: Form data parsing

### Documentation
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- OWASP Authentication: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

### Examples
- FastAPI JWT Example: https://github.com/tiangolo/fastapi/tree/master/docs_src/security
- Refresh Token Rotation: https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/

---

## 🔮 Future Enhancements (Post-Phase 3)

- OAuth2 integration (Google, Facebook login)
- Two-factor authentication (TOTP)
- Session management UI (view/revoke active sessions)
- Login history and audit trail
- Password expiration policy
- IP whitelisting for admins
- Advanced rate limiting (Redis-based)
- Passwordless login (magic links)

---

**Ready to Implement**: This plan provides a complete roadmap for Phase 3 implementation when you're ready to begin.

**Last Updated**: 2025-11-02
