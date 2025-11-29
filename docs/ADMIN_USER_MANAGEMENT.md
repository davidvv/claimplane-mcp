# Admin User Management Guide

This guide explains how to create and manage admin users in the EasyAirClaim platform.

## Table of Contents

- [Overview](#overview)
- [User Roles](#user-roles)
- [Creating Admin Users](#creating-admin-users)
- [Updating User Roles](#updating-user-roles)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

EasyAirClaim uses a role-based access control (RBAC) system with three user roles:

- **Customer**: Regular users who submit flight compensation claims
- **Admin**: Staff who manage claims, review documents, and update claim statuses
- **Superadmin**: Full system access, can promote users and manage admins

All users are stored in the `customers` table with a `role` column that determines their permissions.

---

## User Roles

### Customer (Default)
- Submit flight compensation claims
- Upload supporting documents
- View their own claims
- Receive status updates via email

**Permissions:**
- Access to customer dashboard
- Create new claims
- Upload/view own documents
- View own claim history

### Admin
- Everything a customer can do, plus:
- View all claims in the system
- Review and approve/reject documents
- Update claim statuses
- Add notes to claims (internal and customer-facing)
- Set compensation amounts
- View analytics and reports

**Permissions:**
- Access to admin dashboard (`/admin/*` endpoints)
- Full claim management
- Document review capabilities
- Analytics access

### Superadmin
- Everything an admin can do, plus:
- Promote users to admin/superadmin (future feature)
- System configuration (future feature)
- Delete claims/users (future feature)

---

## Creating Admin Users

### Method 1: Interactive Script (Recommended)

The easiest way to create admin users is using the interactive script:

```bash
# 1. Activate the conda environment
source /Users/david/miniconda3/bin/activate EasyAirClaim

# 2. Navigate to project root
cd /Users/david/Documents/Proyectos/flight_claim

# 3. Run the script
python scripts/create_admin_user.py
```

**The script will prompt you for:**
- Email address
- First name
- Last name
- Phone (optional)
- Role (admin or superadmin)
- Password (hidden input)
- Confirmation

**Example session:**
```
============================================================
EasyAirClaim - Admin User Creation
============================================================

Enter admin user details:

Email address: admin@yourcompany.com
First name: John
Last name: Admin
Phone (optional, press Enter to skip): +34612345678

Select role:
  1. Admin (can manage claims and documents)
  2. Superadmin (full system access)
Enter choice (1 or 2): 1

Password requirements:
  - At least 12 characters
  - Contains uppercase letter
  - Contains lowercase letter
  - Contains digit
  - Contains special character

Password: ************
Confirm password: ************

------------------------------------------------------------
Review details:
  Email: admin@yourcompany.com
  Name: John Admin
  Phone: +34612345678
  Role: admin
------------------------------------------------------------

Create this user? (yes/no): yes

✅ Success! Admin user created:
   ID: 67833bb3-0fc6-4d6c-881d-374b3b971094
   Email: admin@yourcompany.com
   Name: John Admin
   Role: admin
   Active: True
   Email Verified: True

✨ Admin user created successfully!
```

---

### Method 2: Command-Line Mode

For automation or scripts, you can provide all details as command-line arguments:

```bash
python scripts/create_admin_user.py \
  --email admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --first-name John \
  --last-name Admin \
  --phone "+34612345678" \
  --role admin
```

**Create a superadmin:**
```bash
python scripts/create_admin_user.py \
  --email superadmin@yourcompany.com \
  --password "SuperSecurePass456!" \
  --first-name Jane \
  --last-name Superadmin \
  --role superadmin
```

**Notes:**
- Always use quotes around passwords if they contain special characters
- Phone is optional (omit `--phone` flag if not needed)
- Default role is `admin` if `--role` is not specified

---

### Method 3: Direct SQL (Quick Testing Only)

**⚠️ Use only for development/testing. Not recommended for production.**

If you need to quickly promote an existing user to admin:

```bash
# Connect to database
psql -U postgres -d flight_claim

# Update user role
UPDATE customers
SET role = 'admin'
WHERE email = 'user@example.com';

# Verify
SELECT id, email, first_name, last_name, role, is_active
FROM customers
WHERE email = 'user@example.com';
```

**When to use this:**
- Quick testing in development
- Promoting existing users
- Fixing incorrect role assignments

**When NOT to use this:**
- Production environments (use scripts)
- Creating new users (no password hash)
- Batch operations (error-prone)

---

## Updating User Roles

### Promote Customer to Admin

Use the script to check existing user, then update via SQL:

```sql
-- Check current role
SELECT id, email, role FROM customers WHERE email = 'customer@example.com';

-- Promote to admin
UPDATE customers
SET role = 'admin'
WHERE email = 'customer@example.com';

-- Verify
SELECT id, email, role, is_active FROM customers WHERE email = 'customer@example.com';
```

### Demote Admin to Customer

```sql
UPDATE customers
SET role = 'customer'
WHERE email = 'admin@example.com';
```

### Deactivate Admin (Temporarily)

Instead of deleting, you can deactivate:

```sql
UPDATE customers
SET is_active = false
WHERE email = 'admin@example.com';
```

The user will not be able to log in while `is_active = false`.

---

## Security Best Practices

### Password Requirements

Admin passwords MUST meet these requirements:
- ✅ At least 12 characters
- ✅ Contains uppercase letter (A-Z)
- ✅ Contains lowercase letter (a-z)
- ✅ Contains digit (0-9)
- ✅ Contains special character (!@#$%^&*...)

**Good examples:**
- `AdminSecure123!`
- `MyP@ssw0rd2024!`
- `SuperAdmin#456`

**Bad examples:**
- `password` (too short, no complexity)
- `Admin123` (no special character)
- `ADMINPASS!` (no lowercase)

### Storage

- ✅ Passwords are hashed using **bcrypt** before storage
- ✅ Never store plain-text passwords
- ✅ Password hashes are stored in `customers.password_hash`
- ✅ Email addresses are automatically verified for admin users

### Environment Security

**Development:**
- Store admin emails in `.env.local` (gitignored)
- Use strong passwords even in dev
- Never commit `.env` files

**Production:**
- Use environment variables for sensitive data
- Rotate admin passwords regularly (every 90 days recommended)
- Enable 2FA (future enhancement)
- Audit admin actions via logs

### Access Control

Admin endpoints are protected by:
1. **JWT Bearer Token Authentication** - User must be logged in
2. **Role-Based Access Control (RBAC)** - User must have `admin` or `superadmin` role
3. **Token Expiration** - Access tokens expire after 30 minutes (configurable)

**Code example:**
```python
from app.dependencies.auth import get_current_admin

@router.get("/admin/claims")
async def list_claims(admin: Customer = Depends(get_current_admin)):
    # Only users with role 'admin' or 'superadmin' can access
    ...
```

---

## Troubleshooting

### Error: "User with email X already exists"

**Problem:** You're trying to create an admin with an email that's already registered.

**Solutions:**
1. Use a different email address
2. Update the existing user's role (see [Updating User Roles](#updating-user-roles))
3. Delete the existing user first (not recommended)

**Check if user exists:**
```sql
SELECT id, email, role FROM customers WHERE email = 'admin@example.com';
```

---

### Error: "Password does not meet requirements"

**Problem:** Password is too weak.

**Solution:** Use a password that meets all requirements:
```bash
# Generate a secure password
python -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(16)))"
```

---

### Error: "Connection refused" or "Database not found"

**Problem:** Database is not running or `DATABASE_URL` is incorrect.

**Solutions:**

1. **Check if PostgreSQL is running:**
```bash
docker ps | grep postgres
# OR
lsof -i :5432
```

2. **Verify DATABASE_URL in .env:**
```bash
cat .env | grep DATABASE_URL
# Should be: postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim
```

3. **Start database if needed:**
```bash
docker-compose up -d db
```

---

### Error: "Import error: No module named 'app'"

**Problem:** Script is not being run from project root or conda environment is not activated.

**Solution:**
```bash
# 1. Activate conda environment
source /Users/david/miniconda3/bin/activate EasyAirClaim

# 2. Navigate to project root
cd /Users/david/Documents/Proyectos/flight_claim

# 3. Verify Python path
which python
# Should show: /Users/david/miniconda3/envs/EasyAirClaim/bin/python

# 4. Run script
python scripts/create_admin_user.py
```

---

### Can't Login to Admin Dashboard

**Checklist:**
1. ✅ User exists and has `admin` or `superadmin` role
2. ✅ User's `is_active = true`
3. ✅ Using correct email and password
4. ✅ Backend API is running (`http://localhost:8000`)
5. ✅ Admin dashboard is accessible

**Verify user status:**
```sql
SELECT
    id,
    email,
    role,
    is_active,
    is_email_verified,
    password_hash IS NOT NULL as has_password
FROM customers
WHERE email = 'admin@example.com';
```

**Expected output:**
```
role: admin
is_active: true
is_email_verified: true
has_password: true
```

---

## Future Enhancements

The following features are planned for future versions:

- **UI for User Management**: Admins can promote users via dashboard
- **2FA (Two-Factor Authentication)**: Optional 2FA for admin accounts
- **Activity Logs**: Track all admin actions (who did what, when)
- **Password Reset for Admins**: Self-service password reset
- **Session Management**: View and revoke active sessions
- **Audit Trail**: Comprehensive logging of all admin operations

---

## Quick Reference

### Create First Admin
```bash
source /Users/david/miniconda3/bin/activate EasyAirClaim
cd /Users/david/Documents/Proyectos/flight_claim
python scripts/create_admin_user.py
```

### List All Admins
```sql
SELECT id, email, first_name, last_name, role, is_active
FROM customers
WHERE role IN ('admin', 'superadmin')
ORDER BY role, email;
```

### Count Users by Role
```sql
SELECT role, COUNT(*) as count
FROM customers
GROUP BY role;
```

### Check Admin Permissions
Admin users can access:
- `GET /admin/claims` - List all claims
- `GET /admin/claims/{id}` - View claim details
- `PUT /admin/claims/{id}/status` - Update claim status
- `POST /admin/claims/{id}/notes` - Add notes
- `GET /admin/files/*` - File management endpoints
- `GET /admin/analytics/*` - Analytics endpoints (future)

---

## Related Documentation

- [Authentication System](./SECURITY_AUDIT_v0.2.0.md#authentication) - JWT authentication details
- [API Reference](./api-reference.md) - Complete API documentation
- [Database Schema](./database-schema.md) - Database structure

---

**Last Updated:** 2025-11-29
**Version:** v0.2.0
