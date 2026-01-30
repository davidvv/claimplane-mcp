---
name: docker-build-helper
description: Guidelines for handling long-running Docker build processes to avoid timeout errors.
---

# Docker Build Helper Skill

## Purpose
This skill ensures that resource-intensive Docker build operations (especially those involving compilation like `gcc`, `g++`, or large dependency installations) are delegated to the user to run in their local terminal. This prevents timeout errors within the agent environment and ensures build continuity.

## When to Use This Skill
- When modifying `Dockerfile` or `requirements.txt` which triggers a rebuild
- When installing heavy system dependencies (e.g., `build-essential`, `libpq-dev`)
- When previous build attempts have timed out
- When the user's hardware is known to be slow or resource-constrained

## Workflow

### 1. Identify Build Requirement
If a task requires rebuilding a Docker container (e.g., `docker-compose build api` or `docker build .`), assess the likelihood of a long duration.

**Indicators for Delegation:**
- Installing compilers (`gcc`, `g++`, `make`)
- Installing heavy Python libraries (`numpy`, `pandas`, `opencv`, `scipy`)
- Installing system libraries (`libpq-dev`, `libmagic1`)
- History of timeouts on this project

### 2. Instruct the User
Instead of running the build command directly, provide the command to the user clearly.

**Template:**
> ⚠️ **Long-Running Build Required**
> 
> The next step requires rebuilding the Docker container, which may take 10-20 minutes and will likely time out if I run it.
> 
> **Please run this command in your terminal:**
> ```bash
> cd /path/to/project
> docker compose up -d --build <service_name>
> ```
> 
> Let me know when it's done!

### 3. Verify After Completion
Once the user confirms the build is finished, verify the result.

**Verification Commands:**
```bash
# Check container status
docker ps --filter name=<service_name>

# Check if specific package is installed (if applicable)
docker exec <service_name> python -c "import <package>; print('✅ Package installed')"
```

## Anti-Patterns (What NOT to do)
- ❌ Do NOT attempt to run `docker compose build` with a long timeout multiple times.
- ❌ Do NOT try to optimize the build yourself unless asked (e.g., removing dependencies).
- ❌ Do NOT leave the user guessing if the build is running in the background after a timeout.

## Example Interaction

**User:** "I added the new requirements."

**Agent:** "Great! Since we added `numpy` and `scipy`, the build will take a while.

Please run this in your terminal to avoid timeouts:
```bash
cd /home/user/project
docker compose up -d --build api
```

Tell me when it finishes!"
