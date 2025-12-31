# Deployment Guide - For Development Partner

This guide explains how automatic deployments work for the EasyAirClaim project using GitHub Webhooks.

## Overview

When you push code to the `MVP` branch, deployment happens automatically:
1. GitHub sends a webhook notification to the server
2. Server receives the webhook and verifies it's authentic
3. Server pulls the latest code from GitHub
4. Rebuilds Docker containers
5. Deploys the frontend
6. Verifies services are running

**You don't need SSH access to the server** - just push your code and it deploys automatically!

**Perfect for homelab:** Works through Cloudflare Tunnel, no router port forwarding needed!

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

**Unlike GitHub Actions, there's no web UI to watch webhooks.** Instead:

1. **Immediate feedback**: Push completes = webhook sent
2. **Check server logs** (ask David for access):
   ```bash
   sudo journalctl -u webhook-deploy -f
   ```
3. **Wait ~2-3 minutes** then check if your changes are live
4. **Test the application** to verify deployment

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

### "My changes aren't showing up"

1. **Did you push to the right branch?** Must be `MVP` branch
2. **Wait a bit longer:** Frontend build can take 2-3 minutes
3. **Clear browser cache:** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
4. **Check with David:** He can view webhook logs to see if deployment succeeded

### "I pushed but nothing happened"

Possible causes:
- **Wrong branch**: Only `MVP` branch triggers deployment
- **Webhook not configured**: Ask David to check GitHub webhook settings
- **Server down**: Ask David to check if webhook service is running
- **Network issue**: Cloudflare Tunnel might be down

### "Deployment failed mid-way"

Ask David to:
- Check webhook logs: `sudo journalctl -u webhook-deploy -n 50`
- Check deployment script: `bash deploy.sh` manually
- Review Docker logs: `docker-compose logs`

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
- Push broken code (it will deploy broken)
- Push multiple times rapidly (each push triggers a deploy)

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

- **Webhook not triggering?** → Ask David to check webhook service and GitHub settings
- **Deployment script failing?** → Ask David to check `deploy.sh` and server logs
- **Need to see deployment logs?** → Ask David for access to server logs
- **General code questions?** → Feel free to ask!

---

## Technical Details (For Reference)

### Files Involved

- `webhook_deploy.py` - Flask app that receives GitHub webhooks
- `deploy.sh` - Deployment script that runs on the server
- `webhook-deploy.service` - Systemd service that keeps webhook receiver running

### Security

- Webhook requests are verified using HMAC-SHA256 signatures
- Only authenticated webhooks from GitHub are accepted
- Secret token is stored securely on the server (not in code)
- Only pushes to `MVP` branch trigger deployment

### Architecture

```
Your Push → GitHub → Webhook Notification → Cloudflare Tunnel →
  → Webhook Receiver (port 9000) → Verify Signature →
  → Run deploy.sh → Pull Code → Build Docker → Build Frontend →
  → Verify Services → Done ✅
```

**Why this works in homelab:**
- All connections are **outbound** from your server
- No router port forwarding needed
- Uses existing Cloudflare Tunnel infrastructure
- GitHub doesn't need direct access to your network

### Deployment Process Timeline

- 0:00 - You push to GitHub
- 0:01 - GitHub sends webhook notification
- 0:02 - Webhook receiver verifies and starts deployment
- 0:05 - Git pull completed
- 1:00 - Docker rebuild started
- 2:00 - Frontend build started
- 2:30 - Services verified
- 2:45 - Deployment complete ✅

### Webhook Service Status

To check if the webhook service is running (ask David):
```bash
# Check service status
sudo systemctl status webhook-deploy

# View recent logs
sudo journalctl -u webhook-deploy -n 50

# Restart service if needed
sudo systemctl restart webhook-deploy
```

---

## Advantages Over SSH/GitHub Actions

✅ **Security:** No SSH port exposed to internet
✅ **Homelab-friendly:** Works through existing Cloudflare Tunnel
✅ **Cost:** 100% free forever, no CI/CD minutes
✅ **Simple:** Fewer moving parts than GitHub Actions
✅ **Fast:** Near-instant trigger when you push

---

**Happy deploying! 🚀**

Last updated: 2025-12-31
