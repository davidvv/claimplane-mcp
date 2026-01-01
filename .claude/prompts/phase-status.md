# Phase Status Check

Quickly verify the current phase implementation status and identify any discrepancies between ROADMAP.md and actual codebase.

## Instructions

**Execute all steps proactively and provide a concise summary.**

### Step 1: Read Current Roadmap Status
1. Read `ROADMAP.md` header to identify:
   - Current version
   - Current phase
   - Phase percentages/status
2. Note which phase is marked as "IN PROGRESS"

### Step 2: Verify Against Codebase
Use the Task tool with `subagent_type=Explore` to verify implementation:

For the current phase, check:
1. **Database models** - Are required models implemented?
2. **Backend endpoints** - Are routers/services implemented?
3. **Frontend components** - Are UI components implemented?
4. **Integration** - Are frontend and backend connected?

### Step 3: Calculate Actual Completion
Based on what exists in the codebase, determine:
- What's actually implemented (with file references)
- What's marked as done but missing
- What's marked as todo but actually done
- Actual completion percentage

### Step 4: Identify Discrepancies
List any mismatches between ROADMAP.md and reality:
- Items marked ✅ but not implemented
- Items not marked but actually complete
- Percentage mismatches

### Step 5: Report Summary

Provide output in this format:

```
📊 Phase Status Report

Current Phase: Phase X - [Name]
Roadmap Status: X% complete
Actual Status: Y% complete
Discrepancy: ±Z%

✅ What's Complete:
- Item 1 (file: path/to/file.ts)
- Item 2 (file: path/to/file.py)

⏳ What's In Progress:
- Item 3 (partially done)

❌ What's Missing:
- Item 4 (marked done but not found)
- Item 5 (blocked by X)

🔍 Recommendations:
- Update ROADMAP.md percentage to Y%
- Mark Item 4 as incomplete
- Add Item 6 to completed list

Next Steps: [What to work on next]
```

## Execution Notes

- Use Explore agent for codebase verification (be thorough)
- Provide file paths and line numbers as evidence
- Be objective - base assessment on code, not on documentation
- Highlight blocking issues clearly
