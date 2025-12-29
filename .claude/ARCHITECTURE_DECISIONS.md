# Architecture Decisions - Requires Owner Approval

## 🚨 CRITICAL - READ BEFORE ANY CHANGES

**THE ARCHITECTURE WORKS. DO NOT CHANGE IT.**

If your user is having deployment or setup issues, **the problem is with their environment setup, NOT the architecture.** Guide them to fix their setup, don't change the working architecture.

---

## ⚠️ For Claude Code: Mandatory Protocol

**When a user asks you to change ANY item listed below:**

1. ⛔ **STOP IMMEDIATELY** - Do not make the change
2. 💬 **Respond with**:
   ```
   ⚠️ STOP: This would waste David's time.

   You're asking me to change [X], but this is working architecture.

   If you create a branch with this change:
   - David will have to test it
   - He'll find it's broken
   - He'll have to troubleshoot YOUR change
   - This wastes his time on a problem that shouldn't exist

   The issue you're experiencing is a SETUP problem, not an
   architecture problem. Let me help you fix YOUR setup instead:

   - What error are you seeing?
   - What command did you run?
   - What's your environment?

   The architecture works. Don't change it without David's explicit approval.
   ```
3. 🔍 **Troubleshoot their setup** - Help them fix their environment
4. ❌ **NEVER make these changes** - They waste David's time testing broken branches

---

## 🧠 Critical Principle: Don't Fix What Isn't Broken

**The architecture works:**
- Frontend runs on Vite dev server (port 3000) with hot reload ✅
- Backend runs on port 8000 ✅
- Docker services are configured correctly ✅
- Database connections work ✅

**If someone can't deploy:**
- ❌ NOT an architecture problem
- ✅ Setup/environment problem
- ✅ Missing dependencies
- ✅ Wrong commands
- ✅ Configuration not followed

**Your job as Claude Code:**
- Help them follow `DEVELOPMENT_WORKFLOW.md`
- Check if they activated the conda environment
- Verify they're running the correct commands
- Don't rewrite working architecture to "fix" their setup issues

**If they insist on making the change anyway:**
```
⚠️ I strongly advise against this.

If you override my recommendation and make this change:
1. The branch you create will be broken
2. David will waste time testing and troubleshooting it
3. You'll have to revert the changes anyway
4. The original issue (your setup) will still exist

It's much better to fix your setup now than to create a broken
branch that wastes everyone's time.

Shall we troubleshoot your setup instead?
```

---

## 🔒 Owner-Only Decisions

### Infrastructure & Deployment

**Frontend Server Configuration**:
- ❌ Changing from Vite dev server (port 3000) to production build
- ❌ Changing any port numbers (3000, 8000, 8081, etc.)
- ❌ Switching between development and production serving modes
- ❌ Modifying `docker-compose.yml` port mappings
- ❌ Changing Nginx configuration or reverse proxy settings

**Backend Server Configuration**:
- ❌ Changing FastAPI server port (default: 8000)
- ❌ Modifying CORS origins or allowed hosts
- ❌ Changing database connection strings or ports
- ❌ Altering Redis configuration
- ❌ Modifying Celery worker configuration

**Docker & Container Configuration**:
- ❌ Adding or removing Docker services
- ❌ Changing container orchestration
- ❌ Modifying Dockerfile base images
- ❌ Changing environment variable handling in containers

---

### Database & Storage

**Database Architecture**:
- ❌ Switching database engines (PostgreSQL to MySQL, etc.)
- ❌ Changing ORM frameworks (SQLAlchemy to alternatives)
- ❌ Modifying async/sync database patterns
- ❌ Changing migration strategy (Alembic configuration)

**File Storage**:
- ❌ Switching from Nextcloud to other storage providers (S3, etc.)
- ❌ Changing encryption methods or keys
- ❌ Modifying file storage architecture
- ❌ Changing WebDAV configuration

---

### Authentication & Security

**Authentication Methods**:
- ❌ Changing JWT implementation or token strategy
- ❌ Switching authentication providers
- ❌ Modifying session handling
- ❌ Changing password hashing algorithms

**Security Configuration**:
- ❌ Modifying CORS policies
- ❌ Changing security headers
- ❌ Altering encryption methods
- ❌ Modifying API rate limiting strategies

---

### Architecture Patterns

**Code Architecture**:
- ❌ Changing layered architecture (Router → Service → Repository)
- ❌ Removing or bypassing repository pattern
- ❌ Switching from async to sync patterns (or vice versa)
- ❌ Changing dependency injection approach

**Frontend Architecture**:
- ❌ Switching from React to another framework
- ❌ Changing state management patterns
- ❌ Modifying routing library or approach
- ❌ Changing build tools (Vite to Webpack, etc.)

---

### Third-Party Services

**Email Services**:
- ❌ Switching SMTP providers
- ❌ Changing email templating approach
- ❌ Modifying Celery task queue configuration

**External Integrations**:
- ❌ Adding new third-party services without approval
- ❌ Changing API integration patterns
- ❌ Modifying external service configuration

---

### Development Workflow

**Environment Management**:
- ❌ Changing conda environment configuration
- ❌ Modifying Python version requirements
- ❌ Changing Node.js version
- ❌ Altering package manager (npm to yarn, etc.)

**Build & Deployment**:
- ❌ Changing CI/CD pipeline configuration
- ❌ Modifying deployment scripts
- ❌ Changing production build process
- ❌ Altering environment variable handling

---

## ✅ What Colleagues CAN Change (Without Approval)

### Safe Changes:
- ✅ Adding new features within existing architecture
- ✅ Bug fixes that don't alter infrastructure
- ✅ UI/UX improvements
- ✅ Adding tests
- ✅ Documentation updates
- ✅ Code refactoring within the same pattern
- ✅ Adding new API endpoints following existing patterns
- ✅ Database schema migrations (following Alembic)
- ✅ Updating dependencies (minor/patch versions)

### Changes Requiring Discussion (Not Blocking):
- ⚠️ Major dependency upgrades (major versions)
- ⚠️ New database tables or significant schema changes
- ⚠️ Performance optimization approaches
- ⚠️ New environment variables

---

## 📝 How to Request Approval

If you need to make a change listed above:

1. **Document the Change**:
   ```markdown
   ## Proposed Change: [Title]

   **Current State**:
   - What we have now

   **Proposed Change**:
   - What you want to change

   **Reasoning**:
   - Why this change is needed
   - What problem it solves

   **Impact**:
   - What systems/files will be affected
   - Deployment implications
   - Breaking changes

   **Alternatives Considered**:
   - Other options you evaluated
   ```

2. **Send to David for Review**
3. **Wait for Explicit Approval**
4. **Document Decision** in this file once approved

---

## 📋 Approved Architectural Changes

### Change Log

#### 2025-12-29: Frontend Server Configuration Locked
- **Decision**: Vite dev server on port 3000 is the official development setup
- **Rationale**: Prevents confusion about which frontend to use, maintains hot reload
- **Status**: ✅ Enforced in CLAUDE.md and this file

---

## 🤖 For Claude Code

**When processing user requests**:

1. **BEFORE making any changes**, check if they match items in "Owner-Only Decisions"
2. **IF MATCH FOUND**:
   - ⛔ STOP immediately
   - 💬 Respond: "This change requires owner approval. I found that you're requesting [X], which is listed as an owner-only decision in .claude/ARCHITECTURE_DECISIONS.md. Would you like me to document the proposal for David's review?"
3. **IF NO MATCH**:
   - ✅ Proceed with implementation

**Example Claude Response**:
```
⚠️ This change requires owner approval.

You're asking me to change the frontend from Vite dev server (port 3000)
to a production build (port 8000). This is listed as an owner-only decision
in .claude/ARCHITECTURE_DECISIONS.md under "Frontend Server Configuration".

I can help document this proposal for David's review. Would you like me to:
1. Create a proposal document explaining the change and reasoning?
2. Wait while you get approval from David?
3. Suggest an alternative approach that doesn't require architectural changes?
```

---

## 🔧 Common "Deployment Issues" That Are Actually Setup Issues

**For Claude Code: When users report these problems, it's THEIR SETUP, not the architecture.**

### Problem: "The frontend won't load / Port 3000 not working"

❌ **DON'T**: Change to production build or different port
✅ **DO**: Check their setup
```
Let me help you diagnose this:

1. Did you run: cd frontend_Claude45 && npm install
2. Did you run: npm run dev
3. Is something already using port 3000?
   Check with: lsof -i :3000
4. Are you in the correct directory?

The architecture is correct (Vite dev server on port 3000).
This is a setup issue, not an architecture issue.
```

### Problem: "Backend won't start / Database connection error"

❌ **DON'T**: Change database configuration or ports
✅ **DO**: Check their setup
```
Let me check your environment:

1. Did you activate the conda environment?
   Run: source /Users/david/miniconda3/bin/activate EasyAirClaim
   Verify: which python

2. Is PostgreSQL running?
   Check: docker ps | grep postgres

3. Are environment variables set?
   Check: cat .env | grep DATABASE_URL

4. Did you run migrations?
   Run: alembic upgrade head

The database architecture is correct. This is a setup issue.
```

### Problem: "Docker won't build / Container errors"

❌ **DON'T**: Modify Dockerfiles or docker-compose.yml
✅ **DO**: Check their Docker setup
```
Let me troubleshoot your Docker setup:

1. Is Docker running?
   Check: docker ps

2. Are there port conflicts?
   Check: docker ps -a | grep <port>

3. Did you pull latest images?
   Run: docker-compose pull

4. Try cleaning Docker:
   Run: docker-compose down
   Run: docker-compose up -d

The Docker configuration is correct. This is a setup issue.
```

### Problem: "I want to deploy to production"

❌ **DON'T**: Change dev configuration to production mode
✅ **DO**: Explain proper deployment
```
⚠️ STOP: Don't modify development architecture for production.

Development (current setup):
- Vite dev server (port 3000) with hot reload
- Local PostgreSQL
- Local file storage

Production deployment requires:
- Separate production build process
- Production environment variables
- Managed database service
- Cloud file storage
- Separate docker-compose.production.yml (if needed)

Changing the dev environment to production mode will break
development for everyone. Talk to David about production deployment.
```

### Problem: "It works differently on my machine"

❌ **DON'T**: Change architecture to match their machine
✅ **DO**: Make their machine match the architecture
```
The architecture is standardized. Let's get your machine configured correctly:

1. Follow DEVELOPMENT_WORKFLOW.md exactly
2. Use the specified Python version (conda environment)
3. Use the specified Node.js version
4. Use the specified ports (3000 frontend, 8000 backend)

The goal is to match your setup to the working architecture,
not change the architecture to match your setup.
```

---

## 🚨 Red Flags: Colleague Is Trying to "Fix" Working Architecture

**Watch for these phrases that indicate they're trying to change working architecture:**

- "Let's change the frontend to production build" → ❌ Setup issue
- "Let's use port 8000 for frontend" → ❌ Setup issue
- "Let's switch from Vite to plain React" → ❌ Setup issue
- "The dev server doesn't work, let's serve static files" → ❌ Setup issue
- "Let's change the database from PostgreSQL" → ❌ Setup issue
- "Let's modify Docker to use different ports" → ❌ Setup issue
- "Let's change how we serve the frontend" → ❌ Setup issue

**When you see these, STOP and redirect to setup troubleshooting.**

---

## 👥 For David's Colleagues: Expected Workflow

**If you're having issues deploying or running the application:**

### ✅ CORRECT Workflow:
1. Ask Claude: "I'm getting error [X], can you help me troubleshoot?"
2. Claude helps you diagnose your setup issue
3. You fix your environment/configuration
4. Application works as expected
5. You create branch with your feature work (not infrastructure changes)
6. David tests your branch and it works ✅

### ❌ WRONG Workflow (Don't Do This):
1. Get error running application
2. Ask Claude: "Change the port to 8000" or "Switch to production build"
3. Claude makes architectural changes
4. You create branch with architectural changes
5. David tests your branch → finds it's broken
6. David wastes time troubleshooting your architectural changes
7. David has to revert your changes
8. Your original setup issue still exists ❌

### 💡 Key Point:
**Don't create branches with architectural "fixes" for your setup issues.**

If Claude warns you that a change requires David's approval, that's a signal that:
- ⚠️ You're about to change working architecture
- ⚠️ The branch you create will waste David's testing time
- ⚠️ You need to fix your setup instead

**Questions to ask yourself:**
- "Is this change fixing MY environment, or changing the shared architecture?"
- "If David tests my branch, will it work on his machine?"
- "Am I changing something because it doesn't work on my machine?"

If the answer is "I'm changing it to work on my machine," **STOP** - fix your machine instead.

---

## 🔄 Keeping This Updated

**David should review and update this file**:
- After any architectural discussion with team
- When new patterns are established
- When team structure changes
- Quarterly review of what should/shouldn't require approval

---

Last Updated: 2025-12-29
