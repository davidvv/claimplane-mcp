# MVP Plan – EasyAirClaim

## Goal
A minimal, runnable API that lets users:
1. Create and fetch **Customer** records  
2. Create and fetch **Claim** records (linked to a customer)  
3. Health-check endpoint

## Cut from original spec
- ❌ Flight-status lookup (`/flights/status/*`)  
- ❌ Eligibility engine (`/eligibility/check`)  
- ❌ Document upload / download  
- ❌ Authentication & authorization  
- ❌ Redis (drop service entirely)  
- ❌ Pagination (return small arrays inline)  

## Keep (MVP subset)
- ✅ `POST /customers`  
- ✅ `GET  /customers/{customerId}`  
- ✅ `POST /claims`  
- ✅ `GET  /claims/{claimId}`  
- ✅ `GET  /health`

## Data models (SQLAlchemy)
**customers**
- id (uuid pk)  
- email (unique)  
- first_name  
- last_name  
- phone (nullable)  
- street, city, postal_code, country (all nullable)  
- created_at (server default)  
- updated_at (server default)

**claims**
- id (uuid pk)  
- customer_id (fk → customers.id)  
- flight_number (string)  
- airline (string)  
- departure_date (date)  
- departure_airport (string)  
- arrival_airport (string)  
- incident_type (enum: delay, cancellation, denied_boarding, baggage_delay)  
- status (enum: draft, submitted, under_review, approved, rejected, paid, closed)  
- compensation_amount (numeric nullable)  
- currency (string, default 'EUR')  
- notes (text nullable)  
- submitted_at (server default)  
- updated_at (server default)

## Tech stack
- FastAPI (async, auto-docs)  
- SQLAlchemy 2.0 (async session)  
- PostgreSQL 15 (via docker-compose)  
- Nginx (reverse proxy, port 80 → api:8000)  
- Python 3.11 slim container

## Docker services (simplified compose)
- `db` – postgres:15-alpine  
- `api` – our FastAPI container  
- `nginx` – nginx:alpine (no ssl for MVP)

## Folder layout
```
app/
├── __init__.py
├── main.py
├── database.py
├── models.py
├── schemas.py
└── routers/
    ├── __init__.py
    ├── customers.py
    └── claims.py
Dockerfile
docker-compose.yml
nginx.conf
requirements.txt
```

## Next steps
1. Prune OpenAPI yaml → `openapi_mvp.yaml` (manual edit)  
2. Generate / copy-paste Pydantic schemas from pruned spec  
3. Implement SQLAlchemy models  
4. Wire routers & services  
5. Test with curl