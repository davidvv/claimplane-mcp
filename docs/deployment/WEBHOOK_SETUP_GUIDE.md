# Webhook Deployment Setup Guide

This guide shows you (David) how to set up automatic webhook-based deployments for your homelab environment.

## Overview

This setup enables automatic deployments when code is pushed to GitHub, **without requiring SSH port forwarding**. Perfect for homelab environments with Cloudflare Tunnel.

The webhook receiver runs as a Docker container alongside your other services.

---

## Step 1: Start the Webhook Service

The webhook service is already configured in `docker-compose.yml`. Just rebuild and start it:

```bash
# Build the webhook container
docker-compose build webhook

# Start the webhook service
docker-compose up -d webhook

# Check if it's running
docker-compose ps webhook
```

You should see:
```
NAME                    IMAGE                     STATUS
flight_claim_webhook    claimplane-webhook      Up X seconds
```

**Check logs:**
```bash
docker-compose logs webhook -f
```

You should see:
```
Starting webhook receiver on port 9000
Deploy script: /app/deploy.sh
```

---

## Step 2: Test the Webhook Endpoint

```bash
# Test health endpoint
curl http://localhost:9000/health

# Expected response:
# {"status":"healthy","service":"webhook-deploy"}
```

If you get a connection error, check:
```bash
# View logs
docker-compose logs webhook

# Restart if needed
docker-compose restart webhook
```

---

## Step 3: Configure Cloudflare Tunnel

Add a route for the webhook receiver to your Cloudflare Tunnel configuration.

**Option A: Subdomain (Recommended)**

Add to your tunnel config:
```yaml
ingress:
  - hostname: deploy.yourdomain.com
    service: http://localhost:9000
  # ... your other routes ...
  - service: http_status:404
```

**Option B: Path-based routing**

Add to your tunnel config:
```yaml
ingress:
  - hostname: yourdomain.com
    path: /webhook/*
    service: http://localhost:9000
  # ... your other routes ...
  - service: http_status:404
```

**Reload Cloudflare Tunnel:**
```bash
# If running as systemd service
sudo systemctl restart cloudflared

# Or if running in Docker
docker restart <cloudflared-container>
```

---

## Step 4: Configure GitHub Webhook

### Find Your Webhook URL

Based on your Cloudflare Tunnel setup:
- **Option A**: `https://deploy.yourdomain.com/deploy`
- **Option B**: `https://yourdomain.com/webhook/deploy`

### Add Webhook to GitHub Repository

1. Go to: `https://github.com/davidvv/claimplane/settings/hooks`

2. Click **"Add webhook"**

3. Configure:
   - **Payload URL**: Your webhook URL (see above)
   - **Content type**: `application/json`
   - **Secret**: `rgnS_FLumV_OULKyoR4NJIYzmCzdH4NJuMW1yvb81GU`
   - **Which events**: Select "Just the push event"
   - **Active**: ✅ Checked

4. Click **"Add webhook"**

5. GitHub will send a test ping

### Verify Webhook Received

```bash
# Watch webhook logs
docker-compose logs webhook -f
```

You should see GitHub's test ping in the logs.

---

## Step 5: Test Full Deployment

### Make a Test Change

```bash
# Make a small change
echo "# Webhook test $(date)" >> README.md
git add README.md
git commit -m "test: webhook deployment trigger"
git push origin MVP
```

### Watch the Deployment

```bash
# Follow webhook logs
docker-compose logs webhook -f
```

You should see:
```
Deployment triggered by david (1 commits)
Starting deployment script...
Pulling latest code...
Rebuilding Docker containers...
Building frontend...
Deployment completed successfully
```

### Verify Services Restarted

```bash
# Check all services
docker-compose ps

# All should show "Up" status
```

---

## Monitoring and Troubleshooting

### View Webhook Logs

```bash
# Follow logs in real-time
docker-compose logs webhook -f

# View last 50 lines
docker-compose logs webhook --tail=50

# View all logs
docker-compose logs webhook
```

### Check Webhook Service Status

```bash
# Check if running
docker-compose ps webhook

# Restart webhook service
docker-compose restart webhook

# Rebuild and restart
docker-compose up -d --build webhook
```

### Common Issues

#### ❌ Webhook container won't start

**Check logs:**
```bash
docker-compose logs webhook
```

**Common causes:**
- Port 9000 already in use: Change port in `docker-compose.yml`
- Build failed: Run `docker-compose build webhook` to see errors
- Permission issues: Docker socket access denied

**Fix permission issues:**
```bash
# Add your user to docker group (if not already)
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

#### ❌ GitHub webhook shows error

**Check GitHub webhook delivery:**
1. Go to GitHub repo → Settings → Webhooks
2. Click on your webhook
3. Click "Recent Deliveries"
4. Check response status

**Common causes:**
- Cloudflare Tunnel not routing correctly
- Wrong webhook URL
- Webhook container not running: `docker-compose ps webhook`
- Firewall blocking port 9000 (shouldn't be an issue with Cloudflare Tunnel)

#### ❌ Webhook received but deployment fails

**Check deployment script:**
```bash
# Run deployment manually from inside container
docker exec flight_claim_webhook bash /app/deploy.sh
```

**Common causes:**
- Git permissions issue
- Docker socket permissions
- Frontend build errors
- Docker-compose not found in container

**View detailed deployment logs:**
```bash
# Webhook logs show deployment output
docker-compose logs webhook --tail=100
```

#### ❌ Git pull fails with permission denied

The webhook container needs access to pull from GitHub. Make sure:
1. The repository is public, OR
2. You've configured SSH keys or GitHub token

**For private repos, use SSH:**
```bash
# Generate SSH key in container
docker exec flight_claim_webhook ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ""

# Copy public key
docker exec flight_claim_webhook cat /root/.ssh/id_ed25519.pub

# Add to GitHub repo: Settings → Deploy keys → Add deploy key
# Paste the public key and grant read access
```

---

## Security Notes

### Webhook Secret

The secret is stored in two places:
1. **Server**: `docker-compose.yml` (or `.env` file - recommended)
2. **GitHub**: Repository webhook settings

**To use .env file (recommended):**
```bash
# Create/edit .env file
echo "WEBHOOK_SECRET=rgnS_FLumV_OULKyoR4NJIYzmCzdH4NJuMW1yvb81GU" >> .env

# Remove from docker-compose.yml (it will read from .env automatically)
```

**To rotate the secret:**
```bash
# Generate new secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
# Update GitHub webhook settings
# Restart webhook service
docker-compose restart webhook
```

### HTTPS

- Cloudflare Tunnel provides automatic HTTPS
- GitHub requires HTTPS for webhooks (won't work with HTTP)
- Webhook signature verification prevents unauthorized deployments

### Docker Socket Security

The webhook container has access to the Docker socket, which gives it significant power:
- Can start/stop/restart containers
- Can run any docker command

**This is necessary for deployment but be aware:**
- Only trusted code should run in this container
- The container runs with limited privileges (no host network access)
- Webhook signatures prevent unauthorized deployments

### Firewall

No firewall changes needed! Everything runs through Cloudflare Tunnel:
- Port 9000 exposed only to Cloudflare Tunnel
- No router port forwarding required
- All GitHub connections are outbound HTTPS

---

## Architecture Diagram

```
GitHub (Push Event)
    ↓
GitHub Webhook Notification (HTTPS)
    ↓
Cloudflare Tunnel (TLS termination)
    ↓
localhost:9000 → Webhook Container (Docker)
    ↓
Verify HMAC Signature
    ↓
Execute deploy.sh inside container
    ↓
Git Pull (in mounted volume)
    ↓
Docker-compose rebuild (via docker socket)
    ↓
Frontend Build
    ↓
Services Restarted ✅
```

---

## Useful Commands Reference

```bash
# Webhook container management
docker-compose up -d webhook                # Start webhook service
docker-compose stop webhook                 # Stop webhook service
docker-compose restart webhook              # Restart webhook service
docker-compose logs webhook -f              # Follow logs
docker-compose build webhook                # Rebuild container
docker-compose up -d --build webhook        # Rebuild and restart

# Testing
curl http://localhost:9000/health           # Health check
docker exec flight_claim_webhook bash       # Enter container shell

# Manual deployment
docker exec flight_claim_webhook bash /app/deploy.sh

# View all services
docker-compose ps

# Restart all services
docker-compose restart
```

---

## Environment Variables

Add to `.env` file (recommended):

```bash
# Webhook Configuration
WEBHOOK_SECRET=rgnS_FLumV_OULKyoR4NJIYzmCzdH4NJuMW1yvb81GU
WEBHOOK_PORT=9000
```

---

## Next Steps

After setup is complete:
1. ✅ Share `DEPLOYMENT_GUIDE_FOR_PARTNER.md` with your development partner
2. ✅ Test the full workflow: code change → push → auto-deploy
3. ✅ Monitor first few deployments to ensure stability
4. ✅ Consider setting up deployment notifications (optional)
5. ✅ Add webhook secret to `.env` instead of docker-compose.yml

---

## Advantages of Docker Approach

✅ **Isolated**: Dedicated container with own dependencies
✅ **Consistent**: Same environment every time
✅ **Integrated**: Part of your existing Docker stack
✅ **Auto-restart**: Built-in restart policy
✅ **Clean**: No system Python or conda dependencies needed
✅ **Portable**: Works on any Docker host

---

**Setup complete! Your partner can now deploy by simply pushing to the MVP branch.** 🚀

Last updated: 2025-12-31
