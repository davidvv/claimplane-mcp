# MVP Database Schema

## SQL (PostgreSQL)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE customers (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         TEXT NOT NULL UNIQUE,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    phone         TEXT,
    street        TEXT,
    city          TEXT,
    postal_code   TEXT,
    country       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE claims (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id          UUID NOT NULL REFERENCES customers(id),
    flight_number        TEXT NOT NULL,
    airline              TEXT NOT NULL,
    departure_date       DATE NOT NULL,
    departure_airport    TEXT NOT NULL,
    arrival_airport      TEXT NOT NULL,
    incident_type        TEXT CHECK (incident_type IN ('delay','cancellation','denied_boarding','baggage_delay')),
    status               TEXT DEFAULT 'submitted' CHECK (status IN ('draft','submitted','under_review','approved','rejected','paid','closed')),
    compensation_amount  NUMERIC(10,2),
    currency             TEXT DEFAULT 'EUR',
    notes                TEXT,
    submitted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_claims_updated
    BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

## SQLAlchemy Models (async)

```python
from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    id            = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email         = Column(String, unique=True, nullable=False)
    first_name    = Column(String, nullable=False)
    last_name     = Column(String, nullable=False)
    phone         = Column(String, nullable=True)
    street        = Column(String, nullable=True)
    city          = Column(String, nullable=True)
    postal_code   = Column(String, nullable=True)
    country       = Column(String, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    claims = relationship("Claim", back_populates="customer")

class Claim(Base):
    __tablename__ = "claims"
    id                   = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    customer_id          = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    flight_number        = Column(String, nullable=False)
    airline              = Column(String, nullable=False)
    departure_date       = Column(Date, nullable=False)
    departure_airport    = Column(String, nullable=False)
    arrival_airport      = Column(String, nullable=False)
    incident_type        = Column(String, nullable=False)
    status               = Column(String, default="submitted")
    compensation_amount  = Column(Numeric(10,2), nullable=True)
    currency             = Column(String, default="EUR")
    notes                = Column(Text, nullable=True)
    submitted_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at           = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="claims")