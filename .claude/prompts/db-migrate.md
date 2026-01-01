# Database Migration

Create and run Alembic database migrations safely.

## Instructions

Execute migration workflow with safety checks.

### Step 1: Environment Check
1. Verify conda environment is activated:
   ```bash
   which python
   conda info --envs | grep '*'
   ```

2. Check Alembic is installed:
   ```bash
   alembic --version || pip install alembic
   ```

3. Verify database connection:
   ```bash
   # Check if database URL is set
   python -c "from app.config import Config; print('DB URL configured:', bool(Config.DATABASE_URL))"
   ```

### Step 2: Check Current State
1. Check current migration status:
   ```bash
   alembic current
   ```

2. Show migration history:
   ```bash
   alembic history --verbose | head -20
   ```

3. Check for pending migrations:
   ```bash
   alembic heads
   ```

### Step 3: Safety Checks
Before creating/running migrations:

1. **Backup reminder**: Remind user to backup database if production
2. **Check uncommitted changes**:
   ```bash
   git status app/models.py
   ```
3. **Review model changes**: Read `app/models.py` to understand what changed

### Step 4: Create Migration (if needed)
If creating a new migration:

1. Generate migration:
   ```bash
   alembic revision --autogenerate -m "descriptive_message"
   ```

2. Review generated migration:
   - Read the migration file
   - Check upgrade() function
   - Check downgrade() function
   - Verify column types are correct
   - Check for data loss operations (DROP, ALTER TYPE, etc.)

3. **CRITICAL WARNINGS**:
   - Warn if migration drops tables
   - Warn if migration drops columns
   - Warn if migration changes column types (potential data loss)
   - Suggest data migration scripts if needed

### Step 5: Test Migration (Dry Run)
If available, test on development database first:

```bash
# Show SQL that will be executed (dry run)
alembic upgrade head --sql
```

### Step 6: Run Migration
Execute the migration:

```bash
# Upgrade to latest
alembic upgrade head
```

Or specific version:
```bash
# Upgrade to specific revision
alembic upgrade <revision_id>
```

### Step 7: Verify Migration
After running:

1. Check current revision:
   ```bash
   alembic current
   ```

2. Verify tables exist:
   ```bash
   python -c "
   from app.database import engine
   from sqlalchemy import inspect
   inspector = inspect(engine)
   tables = inspector.get_table_names()
   print(f'Tables ({len(tables)}):', ', '.join(tables))
   "
   ```

3. Check for errors in logs

### Step 8: Rollback (if needed)
If migration fails:

```bash
# Downgrade one revision
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade <revision_id>
```

## Common Operations

### Create Initial Migration
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### Add New Column
```bash
# After adding column to model
alembic revision --autogenerate -m "add column_name to table_name"
alembic upgrade head
```

### Remove Column
```bash
# After removing from model
alembic revision --autogenerate -m "remove column_name from table_name"
# REVIEW CAREFULLY - data loss!
alembic upgrade head
```

### Rename Column
```bash
# Alembic can't detect renames, must manually edit migration
alembic revision -m "rename old_name to new_name"
# Edit migration file:
# op.alter_column('table', 'old_name', new_column_name='new_name')
alembic upgrade head
```

### Add New Table
```bash
# After adding model
alembic revision --autogenerate -m "add table_name table"
alembic upgrade head
```

## Report Format

```
🗄️ Database Migration Report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current State:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Revision: abc123def456
Migration: add_account_deletion_fields
Date: 2025-12-06 10:23:45

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action Taken:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Created migration: migrations/versions/abc123_add_cookie_consent.py
✅ Reviewed upgrade/downgrade functions
✅ Applied migration successfully

Changes:
- Added table: cookie_preferences
- Added column: customers.cookie_consent_given (Boolean)
- Added index: idx_cookie_consent_customer_id

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Warnings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

None

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verification:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Migration applied successfully
✅ All tables present (14 tables)
✅ No errors in database connection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Test application with new schema
2. Verify data integrity
3. Commit migration file to git
4. Update documentation if needed
```

## Safety Warnings

**⚠️ CRITICAL CHECKS**:

1. **Before production migration**:
   - Create database backup
   - Test on staging first
   - Have rollback plan
   - Schedule maintenance window

2. **Dangerous operations** (review carefully):
   - DROP TABLE
   - DROP COLUMN
   - ALTER COLUMN TYPE
   - RENAME (requires manual edit)

3. **Data migration**:
   - If changing types, may need data conversion
   - If splitting columns, may need data migration script
   - If adding NOT NULL, may need default values

## Execution Notes

- Always activate conda environment first
- Review autogenerated migrations - they're not always perfect
- Test downgrade before committing migration
- Keep migrations small and focused
- Descriptive migration messages
- Never edit applied migrations (create new one)
