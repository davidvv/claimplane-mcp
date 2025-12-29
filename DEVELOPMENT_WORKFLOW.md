# Development Workflow - CRITICAL RULES

**FOR ALL CLAUDE CODE SESSIONS - READ THIS FIRST**

## Environment Management - MANDATORY

### ⚠️ NEVER INSTALL TO BASE/SYSTEM PYTHON ⚠️

**CRITICAL RULE**: This project uses a dedicated Python virtual environment. You MUST create and activate a virtual environment before running any commands, installing packages, or running tests.

### Initial Setup (One-Time)

**Option 1: Using Conda (Recommended)**
```bash
# Create environment with Python 3.11
conda create -n EasyAirClaim python=3.11

# Activate environment
conda activate EasyAirClaim

# Install all dependencies
pip install -r requirements.txt

# Verify installation
which python  # Should show conda environment path, NOT system Python
python --version  # Should show Python 3.11.x
```

**Option 2: Using venv**
```bash
# Create virtual environment (creates local venv/ directory)
python3.11 -m venv venv

# Activate environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Verify installation
which python  # Should show venv path, NOT system Python
python --version  # Should show Python 3.11.x
```

**Note about venv/:**
- The `venv/` directory is **local to your machine** and **not committed to git**
- Already in `.gitignore` - you should never see it in `git status`
- Each developer creates their own `venv/` directory
- Do NOT modify, commit, or push the `venv/` directory

### Daily Usage

**ALWAYS activate your environment first** before any development work:

```bash
# For conda users
conda activate EasyAirClaim

# For venv users
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Verify you're in the correct environment:**
```bash
which python
# Should NOT show /usr/bin/python or /usr/local/bin/python
# Should show your virtual environment path

python --version
# Should show: Python 3.11.x
```

### Installing New Dependencies

**ALWAYS activate your environment first**, then:

```bash
# Install a new package
pip install package_name

# Update requirements.txt after adding packages
pip freeze > requirements.txt
```

### Running the Application

```bash
# Make sure your virtual environment is activated first!
# (conda activate EasyAirClaim OR source venv/bin/activate)

# Run the application
python app/main.py

# Or with uvicorn (with hot reload)
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Make sure your virtual environment is activated first!
# (conda activate EasyAirClaim OR source venv/bin/activate)

# Run all tests
pytest

# Run specific test file
pytest app/tests/test_compensation_service.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Git Hooks Setup (ONE-TIME SETUP)

**IMPORTANT**: After cloning the repository, install git hooks to protect architecture files.

```bash
# Run the setup script (one-time only)
./scripts/setup-git-hooks.sh
```

**What this does:**
- Installs pre-commit hook that warns when modifying protected files
- Protected files: `CLAUDE.md`, `.claude/`, `.github/CODEOWNERS`
- Prevents accidental changes to architectural decisions
- Requires confirmation if you try to modify these files

**If you see warnings about protected files:**
- These files define architecture that should NOT be changed
- If you have setup/deployment issues, fix YOUR environment, not the architecture
- Only modify these files with explicit approval from David

## Why This Matters

- **Base environment pollution**: Installing packages in base can cause conflicts across projects
- **Dependency isolation**: Each project has its own dependencies
- **Reproducibility**: Other developers can recreate the exact environment from `requirements.txt`
- **System stability**: Keeps the system Python clean
- **Local environments**: Virtual environments (venv/, conda envs) are local and not shared via git
- **No environment conflicts**: Each developer's machine can have different setups without conflicts

## For Future Claude Sessions

When you start a new Claude Code session on this project:

1. ✅ Read this file first
2. ✅ Activate virtual environment (conda activate EasyAirClaim OR source venv/bin/activate)
3. ✅ Verify you're in the right environment (`which python` should NOT show system Python)
4. ✅ Check `.claude/ARCHITECTURE_DECISIONS.md` for protected files
5. ✅ Proceed with development tasks

## Common Mistakes to Avoid

- ❌ Committing `venv/` directory (already in .gitignore)
- ❌ Installing packages to system/base Python
- ❌ Modifying architecture files without approval
- ❌ Running commands without activating virtual environment first
- ❌ Using wrong Python version (must be 3.11.x)

**DO NOT**:
- ❌ Install packages without activating the environment
- ❌ Use the base conda environment
- ❌ Modify system Python
- ❌ **NEVER include "Co-Authored-By: Claude" or anthropic email in commits/docs**
- ❌ **NEVER include AI-generated attribution or emojis unless explicitly requested**

## Environment File

The project dependencies are in:
- `requirements.txt` - Python packages (install with `pip install -r requirements.txt`)

## Checking Your Current Environment

```bash
# Show conda env
echo $CONDA_PREFIX
# Should show: /Users/david/miniconda3/envs/EasyAirClaim (or base if not activated)

# Alternative
conda info --envs
# The active environment has a * next to it
```

## Troubleshooting

If you get "module not found" errors:
1. Check you're in EasyAirClaim environment: `which python`
2. Install missing package: `pip install package_name`
3. Verify installation: `pip list | grep package_name`

---

**Remember**: When in doubt, always check your environment first!
