# Docker Rebuild

Safely rebuild and restart Docker containers with proper cleanup.

## Instructions

Execute Docker rebuild workflow with safety checks and verification.

### Step 1: Pre-Rebuild Checks
1. Check current container status:
   ```bash
   docker compose ps
   ```

2. Check if any containers are running:
   ```bash
   docker compose ps --services --filter "status=running"
   ```

3. Warn about data loss:
   - **If volumes will be removed**: Warn about database data
   - **If .env changed**: Remind about environment variables
   - **If in production**: STOP and require confirmation

### Step 2: Backup Reminders
Remind user to backup if needed:

- Database data (if not using named volumes)
- Any mounted volumes with important data
- .env file configuration

### Step 3: Stop Containers
Stop all running containers:

```bash
docker compose down
```

Or with volume removal (if requested):
```bash
docker compose down -v
```

### Step 4: Clean Up (Optional)
If full cleanup requested:

```bash
# Remove orphaned containers
docker compose down --remove-orphans

# Remove unused images
docker image prune -f

# Remove build cache (if requested)
docker builder prune -f
```

### Step 5: Pull Latest Images
If using remote images:

```bash
docker compose pull
```

### Step 6: Rebuild Images
Rebuild containers:

```bash
# Standard rebuild
docker compose build

# Or rebuild without cache (clean build)
docker compose build --no-cache

# Or rebuild specific service
docker compose build <service-name>
```

### Step 7: Start Containers
Start containers:

```bash
docker compose up -d
```

Or in foreground (for debugging):
```bash
docker compose up
```

### Step 8: Verify Containers
1. Check all containers started:
   ```bash
   docker compose ps
   ```

2. Check logs for errors:
   ```bash
   docker compose logs --tail=50
   ```

3. Check specific service logs if issues:
   ```bash
   docker compose logs api --tail=100
   docker compose logs db --tail=50
   docker compose logs redis --tail=50
   ```

### Step 9: Health Checks
Verify services are healthy:

1. **Database**:
   ```bash
   docker compose exec db pg_isready
   ```

2. **API**:
   ```bash
   curl http://localhost:8000/health || echo "API not responding"
   ```

3. **Redis**:
   ```bash
   docker compose exec redis redis-cli ping
   ```

4. **Frontend** (if applicable):
   ```bash
   curl http://localhost:3000 || echo "Frontend not responding"
   ```

### Step 10: Post-Rebuild Tasks
Check if any post-rebuild tasks needed:

1. Database migrations:
   ```bash
   docker compose exec api alembic upgrade head
   ```

2. Check environment variables loaded:
   ```bash
   docker compose exec api printenv | grep -E "DATABASE_URL|REDIS_URL|NEXTCLOUD" || echo "Check .env file"
   ```

## Common Scenarios

### Scenario 1: Quick Rebuild (Code Changes)
```bash
docker compose down
docker compose build
docker compose up -d
```

### Scenario 2: Full Clean Rebuild
```bash
docker compose down -v
docker image prune -a -f
docker compose build --no-cache
docker compose up -d
```

### Scenario 3: Rebuild Single Service
```bash
docker compose stop api
docker compose build api
docker compose up -d api
```

### Scenario 4: Rebuild After .env Changes
```bash
docker compose down
# .env changes require full recreation, not just restart
docker compose up -d
```

### Scenario 5: Debugging Build Issues
```bash
docker compose down
docker compose build --progress=plain
docker compose up
# Watch logs in foreground
```

## Report Format

```
🐳 Docker Rebuild Report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pre-Rebuild Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running Containers: 5
- api (healthy)
- db (healthy)
- redis (healthy)
- celery_worker (healthy)
- frontend (healthy)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rebuild Actions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Stopped containers
✅ Rebuilt images (no cache)
✅ Started containers
✅ All services healthy

Build Time: 2m 34s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Post-Rebuild Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Container Status:
✅ api - Up 45 seconds (healthy)
✅ db - Up 47 seconds (healthy)
✅ redis - Up 46 seconds (healthy)
✅ celery_worker - Up 44 seconds
✅ frontend - Up 43 seconds

Health Checks:
✅ Database: accepting connections
✅ API: responding on port 8000
✅ Redis: PONG
✅ Frontend: responding on port 3000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Warnings/Issues:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

None

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recent Logs:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[api] INFO: Application startup complete
[db] LOG: database system is ready to accept connections
[redis] Ready to accept connections
[celery_worker] celery@worker ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Test API endpoints
2. Verify database connectivity
3. Check frontend loads correctly
```

## Common Issues & Fixes

**Issue: Port already in use**
```bash
# Find process using port
sudo lsof -i :8000
# Kill process or change port in docker-compose.yml
```

**Issue: Database connection fails**
```bash
# Check database logs
docker compose logs db
# Verify DATABASE_URL in .env
# Try restarting db service
docker compose restart db
```

**Issue: Image build fails**
```bash
# Check Dockerfile syntax
# Verify build context
# Try clean build
docker compose build --no-cache
```

**Issue: Container keeps restarting**
```bash
# Check logs for errors
docker compose logs <service> --tail=100
# Check resource limits
docker stats
```

## Safety Features

**Automatic Checks**:
- Verify docker and docker-compose installed
- Check current status before stopping
- Verify containers started successfully
- Run health checks after start

**Warnings Provided For**:
- Volume removal (data loss)
- Production environment rebuilds
- Database container restarts
- Long-running builds

## Execution Notes

- Always show current status first
- Provide clear progress updates during rebuild
- Show logs if any errors occur
- Verify all services are healthy before reporting success
- Suggest rollback if rebuild fails
- Keep user informed during long builds
