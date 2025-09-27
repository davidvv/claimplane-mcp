# Key Code Snippets for MVP

## app/database.py
```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://flight_claim_user:flight_claim_password@localhost:5432/flight_claim_db")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

## app/main.py
```python
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import customers, claims

app = FastAPI(title="EasyAirClaim MVP", version="0.1.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(claims.router, prefix="/claims", tags=["claims"])

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## app/schemas.py (excerpt)
```python
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional
from uuid import UUID

class CustomerCreate(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    phone: Optional[str] = None
    address: Optional[dict] = None  # inline street/city/postalCode/country

class CustomerOut(BaseModel):
    id: UUID
    email: str
    firstName: str
    lastName: str
    phone: Optional[str]
    address: Optional[dict]
    createdAt: datetime
    updatedAt: datetime

class ClaimCreate(BaseModel):
    customerInfo: CustomerCreate  # inline customer creation
    flightInfo: dict  # minimal flight fields
    incidentType: str  # delay, cancellation, etc.
    notes: Optional[str] = None

class ClaimOut(BaseModel):
    id: UUID
    customerId: UUID
    flightInfo: dict
    incidentType: str
    status: str
    compensationAmount: Optional[float]
    currency: str
    notes: Optional[str]
    submittedAt: datetime
    updatedAt: datetime
```

## app/routers/customers.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Customer
from app.schemas import CustomerCreate, CustomerOut
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=CustomerOut, status_code=201)
async def create_customer(body: CustomerCreate, db: AsyncSession = Depends(get_db)):
    # merge inline address fields
    cust = Customer(
        email=body.email,
        first_name=body.firstName,
        last_name=body.lastName,
        phone=body.phone,
        street=body.address.get("street") if body.address else None,
        city=body.address.get("city") if body.address else None,
        postal_code=body.address.get("postalCode") if body.address else None,
        country=body.address.get("country") if body.address else None,
    )
    db.add(cust)
    await db.commit()
    await db.refresh(cust)
    return cust

@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(customer_id: UUID, db: AsyncSession = Depends(get_db)):
    cust = await db.get(Customer, customer_id)
    if not cust:
        raise HTTPException(404, "Customer not found")
    return cust
```

## app/routers/claims.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Claim, Customer
from app.schemas import ClaimCreate, ClaimOut
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=ClaimOut, status_code=201)
async def create_claim(body: ClaimCreate, db: AsyncSession = Depends(get_db)):
    # create customer if not exists (lookup by email)
    stmt = select(Customer).where(Customer.email == body.customerInfo.email)
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()
    if not customer:
        customer = Customer(
            email=body.customerInfo.email,
            first_name=body.customerInfo.firstName,
            last_name=body.customerInfo.lastName,
            phone=body.customerInfo.phone,
            street=body.customerInfo.address.get("street") if body.customerInfo.address else None,
            city=body.customerInfo.address.get("city") if body.customerInfo.address else None,
            postal_code=body.customerInfo.address.get("postalCode") if body.customerInfo.address else None,
            country=body.customerInfo.address.get("country") if body.customerInfo.address else None,
        )
        db.add(customer)
        await db.flush()  # get id

    claim = Claim(
        customer_id=customer.id,
        flight_number=body.flightInfo["flightNumber"],
        airline=body.flightInfo["airline"],
        departure_date=body.flightInfo["departureDate"],
        departure_airport=body.flightInfo["departureAirport"],
        arrival_airport=body.flightInfo["arrivalAirport"],
        incident_type=body.incidentType,
        notes=body.notes,
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim

@router.get("/{claim_id}", response_model=ClaimOut)
async def get_claim(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    return claim