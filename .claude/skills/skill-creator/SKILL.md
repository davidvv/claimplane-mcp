---
name: skill-creator
description: Guidelines and template for creating high-quality skills that match the project's standards.
---

# Skill Creator Skill

## Purpose
This skill ensures that all new skills created for the project follow a consistent, high-quality structure. It uses the `openproject-task-manager` skill as the gold standard template.

## When to Use This Skill
- When the user asks you to "create a skill" or "save this as a skill"
- When you identify a repeatable complex workflow that should be codified
- When refactoring existing skills to match the project standard

## Structure of a Perfect Skill

Every skill file (`.claude/skills/<skill-name>/SKILL.md`) must follow this exact structure:

### 1. Frontmatter
```yaml
---
name: skill-name-kebab-case
description: Concise, action-oriented description of what the skill does (max 1 sentence).
---
```

### 2. Header
```markdown
# Skill Name Title Case
```

### 3. Purpose & Timing
```markdown
## Purpose
Clear explanation of *why* this skill exists and what problem it solves.

## When to Use This Skill
- Bullet points describing specific triggers
- "When the user asks for X"
- "Before performing action Y"
```

### 4. Workflow (The Core)
Break down the process into numbered steps. Use bold headers for goals.

```markdown
## Workflow Steps

### Step 1: Phase Name
**Goal**: What should be achieved in this step?

1. **Action Item**: Description of action.
   - Specific tool to use (e.g., `grep`, `write`)
   - Example command or parameter
2. **Another Action**: Description.

### Step 2: Phase Name
...
```

### 5. Checklists & Verification
```markdown
## Checklist
- [ ] Item 1
- [ ] Item 2
```

### 6. Anti-Patterns (Optional but Recommended)
```markdown
## Anti-Patterns
- ❌ Do NOT do X
- ❌ Do NOT forget Y
```

## Gold Standard Example
Refer to `.claude/skills/openproject-task-manager/SKILL.md` for the perfect implementation of this structure.

## Creation Workflow

1. **Analyze Request**: Understand the workflow the user wants to save.
2. **Draft Content**: Map the workflow to the structure above.
3. **Create Directory**: `mkdir -p .claude/skills/<skill-name>`
4. **Write File**: Use `write` to save the content to `.claude/skills/<skill-name>/SKILL.md`.
5. **Verify**: Check that the skill appears in the `available_skills` list (by asking the user or checking context).

## Example Prompt Response

**User**: "Create a skill for database migrations."

**Agent**: "I'll create a `database-migration-helper` skill following our standard format."

*Creates file `.claude/skills/database-migration-helper/SKILL.md` with:*
- **Frontmatter**: `name: database-migration-helper`
- **Purpose**: Safe execution of Alembic migrations
- **Workflow**: 1. Backup DB, 2. Generate migration, 3. Review SQL, 4. Apply
- **Checklist**: Backup confirmed, SQL reviewed, Deployment successful
