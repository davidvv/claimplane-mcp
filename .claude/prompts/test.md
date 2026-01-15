# Test Suite Runner

Run the test suite and provide a comprehensive test report.

## Instructions

**Execute all test commands proactively and summarize results.**

### Step 1: Environment Check
1. Verify conda environment is activated:
   ```bash
   which python
   ```
2. If not in ClaimPlane environment, remind user to activate:
   ```bash
   conda activate ClaimPlane
   ```

### Step 2: Run Tests
Execute the test suite with coverage:

```bash
pytest --verbose --tb=short --cov=app --cov-report=term-missing 2>&1
```

If pytest is not available or fails, try:
```bash
python -m pytest --verbose --tb=short 2>&1
```

### Step 3: Analyze Results
Parse the test output to extract:
1. Total tests run
2. Tests passed
3. Tests failed
4. Tests skipped
5. Coverage percentage
6. Modules with low coverage (<80%)

### Step 4: Highlight Failures
If any tests failed:
1. Show the test name
2. Show the failure reason
3. Show the file and line number
4. Suggest potential fixes if obvious

### Step 5: Coverage Analysis
Identify modules that need more test coverage:
1. List files with <80% coverage
2. Highlight critical files (services, routers) with low coverage
3. Suggest which tests should be added

## Report Format

Provide output as:

```
🧪 Test Suite Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
Tests Run: X
Passed: ✅ Y (Z%)
Failed: ❌ A (B%)
Skipped: ⏭️ C
Coverage: D%

Status: [🟢 ALL PASS | 🔴 FAILURES DETECTED | 🟡 WARNINGS]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Failed Tests (if any):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. test_authentication_flow
   File: app/tests/test_auth.py:45
   Error: AssertionError: Expected 200, got 401
   Suggestion: Check if JWT token is being passed correctly

2. test_file_upload
   File: app/tests/test_files.py:78
   Error: FileNotFoundError: test.pdf
   Suggestion: Ensure test fixtures directory exists

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Coverage Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Low Coverage Files (<80%):
- app/services/auth_service.py: 65% (missing: token refresh logic)
- app/routers/admin_claims.py: 72% (missing: bulk operations tests)
- app/services/file_service.py: 58% (missing: error handling tests)

High Coverage Files (>90%):
- app/services/compensation_service.py: 95%
- app/models.py: 92%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Recommendations:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Fix 2 failing tests in test_auth.py and test_files.py
2. Add tests for token refresh logic (auth_service.py:145-178)
3. Add tests for bulk operations (admin_claims.py:234-289)
4. Add error handling tests for file upload scenarios

Priority: [High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Most critical action]
2. [Second priority]
3. [Third priority]
```

## Execution Notes

- Run tests even if environment not activated (show error clearly)
- Parse pytest output carefully (may have ANSI color codes)
- Be specific about file paths and line numbers
- Provide actionable recommendations
- If tests take >30 seconds, show progress indicator
- Don't fail silently - report all errors clearly

## Optional: Specific Test Runs

If user wants to run specific tests, support:
- `pytest app/tests/test_auth.py` - Single file
- `pytest app/tests/test_auth.py::test_login` - Single test
- `pytest -k "auth"` - Tests matching pattern
- `pytest -x` - Stop on first failure
- `pytest --lf` - Run last failed tests
