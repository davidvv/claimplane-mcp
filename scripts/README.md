# Scripts Directory

This directory contains utility scripts for managing and maintaining the ClaimPlane platform.

## Available Scripts

### `create_admin_user.py` ⭐ NEW
**Purpose:** Create admin and superadmin users for the platform.

**Usage:**
```bash
# Interactive mode (recommended)
python scripts/create_admin_user.py

# Command-line mode
python scripts/create_admin_user.py --email admin@example.com --password "SecurePass123!" --first-name John --last-name Doe --role admin
```

**Documentation:** See [docs/ADMIN_USER_MANAGEMENT.md](../docs/ADMIN_USER_MANAGEMENT.md)

**When to use:**
- Creating the first admin user
- Adding new admin staff members
- Promoting users to superadmin

---

### `generate_secrets.py`
**Purpose:** Generate secure encryption keys and secrets for the application.

**Usage:**
```bash
python scripts/generate_secrets.py
```

**When to use:**
- Initial project setup
- Rotating encryption keys
- Generating new `FILE_ENCRYPTION_KEY` or `SECRET_KEY`

---

### `init_file_validation_rules.py`
**Purpose:** Initialize default file validation rules in the database.

**Usage:**
```bash
python scripts/init_file_validation_rules.py
```

**When to use:**
- First-time database setup
- Resetting file validation rules
- After adding new document types

---

### `test_nextcloud_integration.py`
**Purpose:** Test Nextcloud WebDAV connection and file operations.

**Usage:**
```bash
python scripts/test_nextcloud_integration.py
```

**When to use:**
- Verifying Nextcloud configuration
- Debugging file upload issues
- Testing WebDAV connectivity

---

### Shell Scripts

**`setup_nextcloud.sh`**: Set up Nextcloud container and configuration
**`setup_production_env.sh`**: Configure production environment
**`cleanup-claude-branches.sh`**: Clean up old Git branches

---

## Prerequisites

All Python scripts require:

1. **Conda environment activated:**
   ```bash
   source /Users/david/miniconda3/bin/activate ClaimPlane
   ```

2. **Run from project root:**
   ```bash
   cd /Users/david/Documents/Proyectos/flight_claim
   ```

3. **Environment variables configured:**
   - `.env` file exists with correct `DATABASE_URL`
   - PostgreSQL is running

---

## Quick Start: Create Your First Admin

```bash
# 1. Activate environment
source /Users/david/miniconda3/bin/activate ClaimPlane

# 2. Run interactive script
python scripts/create_admin_user.py

# 3. Follow prompts to create admin user
```

See full documentation: [docs/ADMIN_USER_MANAGEMENT.md](../docs/ADMIN_USER_MANAGEMENT.md)

---

**Last Updated:** 2025-11-29
