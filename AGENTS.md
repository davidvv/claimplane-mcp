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

## Notifications
- **CRITICAL**: If a task takes longer than 10 minutes, or after significant work (bugfixing, testing, new features), send a concise summary to David via RocketChat DM.
- **Pre-approved Path**: The folder `/home/david/rocket-connection` is pre-approved for notification use. Permissions are already configured in `~/.config/opencode/opencode.json`, so you can use it without asking for permission.

**How to notify**:
```bash
cd /home/david/rocket-connection && node -e "
const RocketChatClient = require('./rocketChatClient');
(async () => {
  const client = new RocketChatClient();
  await client.login();
  await client.sendMessage('@david', 'Your message here');
})();
"
```


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