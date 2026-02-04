# AGENTS.md

## Startup Commands
```bash
./start-dev.sh  # Always use this to start all containers (Nextcloud + app)
```

**Important**: Always use `./start-dev.sh` to start the system. This script starts:
1. Nextcloud services (required for file uploads)
2. Main application services (API, workers, nginx)
3. Vite development server on **Port 3000** (Connected to Cloudflare Tunnel)

**CRITICAL: Development Workflow**
- **ALWAYS** use `./start-dev.sh`.
- **Frontend**: Running on **Port 3000** via Vite.
- **NO MANUAL BUILDS**: Do not run `npm run build` or manually restart Nginx for UI changes. Vite handles automatic builds/updates. This prevents frequent environment breakages.

**⚠️ Troubleshooting 502 Bad Gateway**
If you encounter **502 Bad Gateway** errors on `eac.dvvcloud.work`:
1. **CHECK VITE FIRST**: The frontend server (`npm run dev`) runs directly on the host, NOT in Docker.
   - Run `ps aux | grep vite` to see if it's running.
   - If not, start it manually: `cd frontend_Claude45 && npm run dev -- --host &`
2. Check Cloudflare Tunnel: `docker logs unruffled_johnson`
3. Check API: `docker logs flight_claim_api`

Starting individual containers with `docker-compose up` without Nextcloud will cause upload failures that appear successful to users.

## Build/Test Commands
```bash
source /Users/david/miniconda3/bin/activate ClaimPlane
pytest tests/test_specific.py::test_name -v  # Single test
pytest --cov=app --cov-report=html           # Coverage
uvicorn app.main:app --reload                # Dev server
celery -A app.celery_app worker --loglevel=info  # Background tasks
```

## Test Data

### Test Accounts
| Purpose | Email | Notes |
|---------|-------|-------|
| Cloudflare Access | idavidvv@gmail.com | Use this to pass Cloudflare tunnel authentication |
| ClaimPlane Admin | vences.david@icloud.com | Superadmin account for ClaimPlane admin panel |

### Eligible Flights for E2E Testing
| Flight | Date | Route | Delay | Compensation |
|--------|------|-------|-------|--------------|
| UA988 | 2025-08-18 | EWR → FRA | 3+ hours | Eligible |

## OpenProject Task Management

For significant work or feature implementation, you may use the `openproject-task-manager` skill to track progress if needed, but prioritize direct action for straightforward tasks.

## 🛑 CRITICAL NOTIFICATION MANDATE
**NOTIFICATIONS ARE NOT OPTIONAL.** A task is **FAILED** if `rocketchat_send_message` is not called before the final summary.

**IMMEDIATELY** notify @david on:
1. ✅ **Completion**: When you finish a requested task.
2. 🔴 **Failure**: If a build, test, or API check fails.
3. 🔄 **State Change**: e.g., API status updates.

**Format**: `rocketchat_send_message(channel="@david", message="<emoji> <Summary>")`
**❌ NEVER** ask "Should I notify you?". **❌ NEVER** use channel "general".


## Code Style
- **Imports**: Standard lib → 3rd party → local, absolute imports only
- **Types**: Full type hints, async/await everywhere, Pydantic models for validation
- **Naming**: snake_case variables/functions, PascalCase classes, UPPER_SNAKE_CASE constants
- **Error handling**: Service layer raises domain exceptions, routers return HTTPException
- **Patterns**: Repository pattern (never query models directly), service orchestration, dependency injection
- **Formatting**: 88 char line limit, single quotes, trailing commas, async def everywhere

## Agent-Browser tool
- Use `agent-browser` for web interactions
- Start calling the --help: `agent-browser --help`
- Always use `agent-browser` for web interactions
- Never use `browser` directly

---

## 🚨 CRITICAL: SKILL AND AGENT FILE PROTECTION RULES 🚨

### **STRICT PROHIBITION - DO NOT MODIFY WITHOUT EXPLICIT PERMISSION**

**⚠️ MANDATORY RULE**: These files are **PROTECTED ASSETS** and require **DIRECT USER PERMISSION** before any modification:

#### **FORBIDDEN ACTIONS WITHOUT PERMISSION:**
- ❌ **DO NOT** create, modify, delete, or move any files in:
  - `/home/david/.config/opencode/agents/` (Global agent definitions)
  - `/home/david/.config/opencode/skill/` (Global skill definitions)
  - `/home/david/claimplane/claimplane/.claude/agents/` (Project agents)
  - `/home/david/claimplane/claimplane/.claude/skills/` (Project skills)
- ❌ **DO NOT** update, rename, or remove skill/agent files
- ❌ **DO NOT** change skill configurations or metadata
- ❌ **DO NOT** deprecate or mark skills as obsolete
- ❌ **DO NOT** modify the structure or organization of these directories

#### **MANDATORY PERMISSION PROTOCOL:**
1. **ALWAYS ASK FIRST**: "Do you want me to modify skill/agent files?"
2. **GET EXPLICIT CONFIRMATION**: Wait for clear "YES" or approval
3. **DESCRIBE CHANGES**: Explain exactly what will be modified and why
4. **CONFIRM UNDERSTANDING**: Ensure user understands the implications

#### **WHY THIS PROTECTION EXISTS:**
- **Historical Context**: Skill files were removed on Jan 29, 2026, causing workflow disruption
- **Critical Infrastructure**: These files define core development workflows
- **Irreplaceable Knowledge**: Contains project-specific processes and standards
- **Workflow Dependencies**: Other tools and processes depend on these definitions

#### **IF USER REQUESTS CHANGES:**
- ✅ **Document the request** in the session
- ✅ **Backup existing files** before making changes
- ✅ **Test thoroughly** after modifications
- ✅ **Update documentation** to reflect changes
- ✅ **Confirm changes work** with the user

#### **EMERGENCY EXCEPTIONS:**
Only modify without permission if:
- 🚨 **CRITICAL SECURITY VULNERABILITY** discovered in skill files
- 🔥 **SYSTEM BREAKING ERROR** that prevents project operation
- ⚠️ **DATA CORRUPTION RISK** that threatens project integrity

**In emergencies**: Make minimal changes needed, document everything, notify immediately.

---

## Available Skills and Agents

### **GLOBAL SKILLS** (in `/home/david/.config/opencode/skill/`)
Use with: `skill("skill-name")`

- **`commit-workflow`**: Enforces proper commit practices, version tagging, and roadmap maintenance
- **`docker-build-helper`**: Guidelines for handling long-running Docker build processes
- **`git-pull-reminder`**: Ensures Claude Code always pulls latest changes from GitHub
- **`notify-phone`**: Send direct messages to David via RocketChat for important events
- **`openproject-task-manager`**: Manages OpenProject task lifecycle (create, track, log time)
- **`skill-creator`**: Guidelines for creating high-quality skills that match project standards
- **`plugin-creator`**: Guidelines and instructions for creating plugins in OpenCode
- **`subagent-creator`**: Guidelines and instructions for creating specialized subagents

### **GLOBAL AGENTS** (in `/home/david/.config/opencode/agents/`)
Use with: `@agent-name` or `task(subagent_type="agent-name")`

- **`@backend-expert`**: Expert in FastAPI, Celery, Pydantic, and backend architecture
- **`@code-reviewer`**: Reviews code for quality, security, and project-specific conventions
- **`@docs-expert`**: Expert in technical documentation, maintaining READMEs and technical folders
- **`@frontend-expert`**: Expert in React, Tailwind CSS, Vite, and modern frontend development
- **`@law-expert`**: Expert in American and European digital law (GDPR, CCPA)
- **`@security-expert`**: Expert in cybersecurity, penetration testing, and secure coding practices
- **`@test-expert`**: Expert in testing strategies, specifically Pytest, Unit testing, and Integration testing
- **`@troubleshooter`**: Specialized in interpreting logs, tracebacks, and system errors
- **`@web-browser-tester`**: Specialized web browser automation agent for testing applications

### **PROJECT-SPECIFIC** (in `/home/david/claimplane/claimplane/.claude/`)
- **`backend-tester.md`**: Backend testing agent for the ClaimPlane project

---

## Skill Usage Guidelines

### **Loading Skills**
```python
# Load a specific skill
skill("commit-workflow")

# Check available skills
skill()  # Shows available skills
```

### **Invoking Agents**
```python
# Direct mention (manual)
@backend-expert help me review this API code

# Programmatic invocation
task(description="Review backend code", subagent_type="backend-expert")
```

### **Best Practices**
- **Use skills proactively** when they match your current task
- **Always check skill documentation** before using complex skills
- **Follow skill workflows exactly** - they're designed for optimal results
- **Report issues** if skills don't work as expected
- **Suggest improvements** if workflows could be better

---

**⚠️ REMINDER**: These files were removed on January 29, 2026, causing significant workflow disruption. They have been restored to maintain project continuity. **DO NOT REMOVE OR MODIFY WITHOUT EXPLICIT PERMISSION.**

**Version**: 2.0 (2026-02-02) - Added strict protection rules after historical removal incident

---

## 📜 Historical Context

### **The Great Skill Removal Incident of January 29, 2026**

On **January 29, 2026**, multiple critical skill files were removed from the project with commit `7720fb50e9d57f39386789703f6f6004bd146e71` titled "Update AGENTS.md and remove deprecated skill files". This caused significant workflow disruption:

**Skills Removed:**
- `commit-workflow` (593 lines) - Critical commit process documentation
- `docker-build-helper` (73 lines) - Docker build guidelines
- `git-pull-reminder` (98 lines) - Git workflow automation
- `notify-phone` (187 lines) - Notification system
- `openproject-task-manager` (100 lines) - Task management automation
- `skill-creator` (97 lines) - Skill development guidelines

**Impact:**
- Loss of standardized development workflows
- Disruption of automated task management
- Break in commit quality enforcement
- Missing notification capabilities
- Confusion about proper development procedures

**Restoration:**
These skills have been restored to maintain project continuity and prevent future workflow disruptions.

**Lesson Learned:**
Skill and agent files are **critical infrastructure** that should never be removed without explicit user permission and careful consideration of dependencies.