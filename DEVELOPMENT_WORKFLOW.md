# Development Workflow - CRITICAL RULES

**FOR ALL CLAUDE CODE SESSIONS - READ THIS FIRST**

## Environment Management - MANDATORY

### ⚠️ NEVER INSTALL TO BASE ENVIRONMENT ⚠️

**CRITICAL RULE**: This project uses a dedicated conda environment called **EasyAirClaim**. You MUST activate this environment before running any commands, installing packages, or running tests.

### Conda Environment Setup

1. **Check available environments**:
   ```bash
   /Users/david/miniconda3/bin/conda env list
   ```

2. **Activate EasyAirClaim environment**:
   ```bash
   source /Users/david/miniconda3/bin/activate EasyAirClaim
   ```

3. **Verify you're in the correct environment**:
   ```bash
   which python
   # Should output: /Users/david/miniconda3/envs/EasyAirClaim/bin/python

   python --version
   # Should output: Python 3.11.13
   ```

### Installing Dependencies

**ALWAYS activate the EasyAirClaim environment first**, then:

```bash
# For conda packages
conda install package_name

# For pip packages
pip install package_name
```

### Running the Application

```bash
# Activate environment first
source /Users/david/miniconda3/bin/activate EasyAirClaim

# Run the application
python app/main.py

# Or with uvicorn
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Activate environment first
source /Users/david/miniconda3/bin/activate EasyAirClaim

# Run all tests
pytest

# Run specific test file
pytest app/tests/test_compensation_service.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Why This Matters

- **Base environment pollution**: Installing packages in base can cause conflicts across projects
- **Dependency isolation**: Each project has its own dependencies
- **Reproducibility**: Other developers can recreate the exact environment
- **System stability**: Keeps the system Python clean

## For Future Claude Sessions

When you start a new Claude Code session on this project:

1. ✅ Read this file first
2. ✅ Activate EasyAirClaim conda environment
3. ✅ Verify you're in the right environment
4. ✅ Proceed with development tasks

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
