# MVP File Tree

```
.
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, lifespan, middleware
│   ├── database.py       # async engine & sessionmaker
│   ├── models.py         # SQLAlchemy Customer & Claim
│   ├── schemas.py        # Pydantic request/response models
│   └── routers/
│       ├── __init__.py
│       ├── customers.py  # POST /customers, GET /customers/{id}
│       └── claims.py     # POST /claims,    GET /claims/{id}
├── Dockerfile
├── docker-compose.yml    # postgres + api + nginx (no redis)
├── nginx.conf            # reverse proxy :80 → api:8000
├── requirements.txt
└── README.md