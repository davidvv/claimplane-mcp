# AGENTS.md

## Startup Commands
```bash
./start-dev.sh  # Always use this to start all containers (Nextcloud + app)
```

**Important**: Always use `./start-dev.sh` to start the system. This script starts:
1. Nextcloud services (required for file uploads)
2. Main application services (API, workers, nginx)
3. Vite development server

Starting individual containers with `docker-compose up` without Nextcloud will cause upload failures that appear successful to users.

## Build/Test Commands
```bash
source /Users/david/miniconda3/bin/activate EasyAirClaim
pytest tests/test_specific.py::test_name -v  # Single test
pytest --cov=app --cov-report=html           # Coverage
uvicorn app.main:app --reload                # Dev server
celery -A app.celery_app worker --loglevel=info  # Background tasks
```

## Code Style
- **Imports**: Standard lib → 3rd party → local, absolute imports only
- **Types**: Full type hints, async/await everywhere, Pydantic models for validation
- **Naming**: snake_case variables/functions, PascalCase classes, UPPER_SNAKE_CASE constants
- **Error handling**: Service layer raises domain exceptions, routers return HTTPException
- **Patterns**: Repository pattern (never query models directly), service orchestration, dependency injection
- **Formatting**: 88 char line limit, single quotes, trailing commas, async def everywhere