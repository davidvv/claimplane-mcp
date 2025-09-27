# docker-compose.yml (MVP – no Redis)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: flight_claim_db
    environment:
      POSTGRES_DB: flight_claim_db
      POSTGRES_USER: flight_claim_user
      POSTGRES_PASSWORD: flight_claim_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flight_claim_user -d flight_claim_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: flight_claim_api
    environment:
      DATABASE_URL: postgresql+asyncpg://flight_claim_user:flight_claim_password@db:5432/flight_claim_db
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads   # optional, if we add docs later
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: flight_claim_nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data: