# AGENTS.md - Development Guidelines

## Environment Setup
```bash
source /Users/david/miniconda3/bin/activate EasyAirClaim
```

## Commands
- **Run**: `uvicorn app.main:app --reload`
- **Test all**: `pytest`
- **Test single**: `pytest app/tests/test_compensation_service.py -v`
- **Coverage**: `pytest --cov=app --cov-report=html`
- **Celery**: `celery -A app.celery_app worker --loglevel=info`

## Code Style
- **Async everywhere**: Use async/await consistently
- **Repository pattern**: Never query models directly from routers
- **Service layer**: Business logic belongs in services
- **Imports**: Group stdlib, third-party, local imports
- **Types**: Use type hints for all function signatures
- **Naming**: snake_case for variables, PascalCase for classes
- **Error handling**: Use specific exceptions, never catch Exception bare

## Architecture Rules
- Routers: Thin HTTP handlers only
- Services: Orchestrate business logic
- Repositories: Database access via async SQLAlchemy
- Models: SQLAlchemy ORM with validators
- All files encrypted at rest with Fernet

## Testing
- Use pytest-asyncio for async functions
- Use httpx.AsyncClient for API testing
- Aim for 80%+ coverage
- Test edge cases and error scenarios

## Security
- Never commit secrets or keys
- Use parameterized queries (avoid SQL injection)
- Validate all inputs
- Follow secure coding practices