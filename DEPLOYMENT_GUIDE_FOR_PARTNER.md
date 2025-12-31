# Deployment Guide - For Development Partner

This guide explains how automatic deployments work for the EasyAirClaim project using GitHub Actions.

## Overview

When you push code to the `MVP` branch, GitHub Actions automatically:
1. Connects to the production server via SSH
2. Pulls the latest code
3. Rebuilds Docker containers
4. Deploys the frontend
5. Verifies services are running

**You don't need SSH access to the server** - just push your code and it deploys automatically!

---

## Your Development Workflow

### Making Changes

```bash
# 1. Pull latest changes
git pull origin MVP

# 2. Create a feature branch (recommended)
git checkout -b feature/my-new-feature

# 3. Make your changes
# ... edit code ...

# 4. Test locally
# Backend: python app/main.py
# Frontend: cd frontend_Claude45 && npm run dev

# 5. Commit your changes
git add .
git commit -m "feat: add my new feature"

# 6. Merge to MVP branch
git checkout MVP
git merge feature/my-new-feature

# 7. Push to trigger deployment
git push origin MVP
```

### Watching the Deployment

1. Go to the GitHub repository
2. Click the **Actions** tab
3. You'll see your deployment running
4. Click on it to see live logs
5. Wait ~2-3 minutes for completion

### Deployment Status

- ✅ **Green checkmark**: Deployment succeeded, your changes are live!
- ❌ **Red X**: Deployment failed, check the logs to see what went wrong
- 🟡 **Yellow circle**: Deployment in progress

---

## What Gets Deployed

### Backend (FastAPI + Docker)
- Pulls latest code
- Rebuilds Docker containers (PostgreSQL, Redis, API, Celery)
- Restarts all services

### Frontend (Next.js)
- Installs new dependencies (if `package.json` changed)
- Builds production bundle
- Deploys static files

---

## Troubleshooting

### "Deployment failed" - What to do?

1. **Check the GitHub Actions logs:**
   - Go to Actions tab → Click on failed workflow
   - Read the error message

2. **Common issues:**
   - **Syntax error in code**: Fix locally, push again
   - **Docker build failed**: Check `docker-compose.yml` or Dockerfile
   - **Tests failed**: Run tests locally first (`pytest`)
   - **Port conflicts**: Services might already be running

3. **Ask David:** If the error mentions server configuration, SSH access, or deployment scripts, David needs to fix it on the server side.

### "My changes aren't showing up"

1. **Check deployment status:** Green checkmark in Actions tab?
2. **Clear browser cache:** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. **Check correct branch:** Did you push to `MVP`?
4. **Wait a bit longer:** Frontend build can take 2-3 minutes

### "I pushed but deployment didn't trigger"

- Check you pushed to the `MVP` branch (not `main` or another branch)
- Look in Actions tab - might be queued behind another deployment

---

## Best Practices

### Before Pushing

✅ **DO:**
- Test your changes locally
- Run tests: `pytest`
- Check code quality: `ruff check app/`
- Pull latest changes before merging to MVP
- Write clear commit messages (see `.claude/skills/commit-workflow.md`)

❌ **DON'T:**
- Push directly to MVP without testing
- Push multiple times rapidly (wastes CI minutes)
- Push broken code (it will fail deployment)

### Commit Message Format

Follow Conventional Commits (enforced by pre-commit hooks):

```bash
feat: add user authentication
fix: resolve CORS issue on login endpoint
refactor: optimize database queries
docs: update API documentation
test: add tests for compensation calculation
```

---

## GitHub Actions Free Tier Limits

- **2,000 minutes/month** for private repos
- Each deployment takes ~2-3 minutes
- That's ~1,000 deployments/month (plenty!)

If we run out (unlikely), deployments will queue until next month or we can upgrade.

---

## Emergency: Reverting a Deployment

If you pushed something that broke production:

### Option 1: Quick Revert (Recommended)

```bash
# Revert the last commit
git revert HEAD

# Push to trigger new deployment with reverted code
git push origin MVP
```

### Option 2: Force Rollback

```bash
# Go back to previous commit
git reset --hard HEAD~1

# Force push (use with caution!)
git push origin MVP --force
```

⚠️ **Note:** Force pushing will trigger a new deployment, but use it sparingly as it rewrites history.

---

## Questions?

- **GitHub Actions not working?** → Ask David to check server configuration
- **Deployment script failing?** → Ask David to check `deploy.sh`
- **Need different deployment behavior?** → Ask David to modify `.github/workflows/deploy.yml`
- **General code questions?** → Feel free to ask!

---

## Technical Details (For Reference)

### Files Involved

- `.github/workflows/deploy.yml` - GitHub Actions workflow definition
- `deploy.sh` - Deployment script that runs on the server
- Server has a dedicated SSH key that GitHub uses to connect

### Security

- GitHub connects using a dedicated SSH key (not your personal key)
- The SSH key is stored as a GitHub Secret (encrypted)
- Only authorized collaborators can trigger deployments
- Deployment logs are visible in GitHub Actions

### Deployment Process

```
Your Push → GitHub → SSH to Server → Pull Code → Build Docker → Build Frontend → Verify → Done
```

Full deployment timeline:
- 0:00 - GitHub receives push
- 0:05 - Workflow starts
- 0:10 - SSH connection established
- 0:15 - Git pull completed
- 1:00 - Docker rebuild started
- 2:00 - Frontend build started
- 2:30 - Services verified
- 2:45 - Deployment complete ✅

---

**Happy deploying! 🚀**

Last updated: 2025-12-29
