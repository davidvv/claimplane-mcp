"""Pydantic schemas for request/response validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class AddressSchema(BaseModel):
    """Address schema for customer address information."""
    
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20, alias="postalCode")
    country: Optional[str] = Field(None, max_length=100)
    
    class Config:
        populate_by_name = True


class CustomerCreateSchema(BaseModel):
    """Schema for creating a new customer."""
    
    email: EmailStr
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    class Config:
        populate_by_name = True


class CustomerUpdateSchema(BaseModel):
    """Schema for updating a customer (PUT - all fields required)."""
    
    email: EmailStr
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    class Config:
        populate_by_name = True


class CustomerPatchSchema(BaseModel):
    """Schema for partially updating a customer (PATCH - only specified fields updated)."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50, alias="firstName")
    last_name: Optional[str] = Field(None, max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[AddressSchema] = None
    
    class Config:
        populate_by_name = True


class CustomerResponseSchema(BaseModel):
    """Schema for customer response."""
    
    id: UUID
    email: EmailStr
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    phone: Optional[str]
    address: Optional[AddressSchema]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FlightInfoSchema(BaseModel):
    """Flight information schema."""
    
    flight_number: str = Field(..., alias="flightNumber", min_length=3, max_length=10)
    airline: str = Field(..., max_length=100)
    departure_date: date = Field(..., alias="departureDate")
    departure_airport: str = Field(..., alias="departureAirport", min_length=3, max_length=3)
    arrival_airport: str = Field(..., alias="arrivalAirport", min_length=3, max_length=3)
    
    @validator('departure_airport', 'arrival_airport')
    def validate_airport_code(cls, v):
        """Validate airport codes are uppercase."""
        return v.upper()
    
    @validator('flight_number')
    def validate_flight_number(cls, v):
        """Validate flight number format."""
        return v.upper()
    
    class Config:
        populate_by_name = True


class ClaimCreateSchema(BaseModel):
    """Schema for creating a new claim."""
    
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimUpdateSchema(BaseModel):
    """Schema for updating a claim (PUT - all fields required)."""
    
    customer_id: UUID = Field(..., alias="customerId")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimPatchSchema(BaseModel):
    """Schema for partially updating a claim (PATCH - only specified fields updated)."""
    
    customer_id: Optional[UUID] = Field(None, alias="customerId")
    flight_info: Optional[FlightInfoSchema] = Field(None, alias="flightInfo")
    incident_type: Optional[str] = Field(None, alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type if provided."""
        if v is not None:
            valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
            if v not in valid_types:
                raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class ClaimResponseSchema(BaseModel):
    """Schema for claim response."""
    
    id: UUID
    customer_id: UUID = Field(..., alias="customerId")
    flight_number: str = Field(..., alias="flightNumber")
    airline: str
    departure_date: date = Field(..., alias="departureDate")
    departure_airport: str = Field(..., alias="departureAirport")
    arrival_airport: str = Field(..., alias="arrivalAirport")
    incident_type: str = Field(..., alias="incidentType")
    status: str
    compensation_amount: Optional[Decimal] = Field(None, alias="compensationAmount")
    currency: str = "EUR"
    notes: Optional[str]
    submitted_at: datetime = Field(..., alias="submittedAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class ClaimRequestSchema(BaseModel):
    """Schema for claim request with customer info."""
    
    customer_info: CustomerCreateSchema = Field(..., alias="customerInfo")
    flight_info: FlightInfoSchema = Field(..., alias="flightInfo")
    incident_type: str = Field(..., alias="incidentType")
    notes: Optional[str] = None
    
    @validator('incident_type')
    def validate_incident_type(cls, v):
        """Validate incident type."""
        valid_types = ["delay", "cancellation", "denied_boarding", "baggage_delay"]
        if v not in valid_types:
            raise ValueError(f"Incident type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        populate_by_name = True


class HealthResponseSchema(BaseModel):
    """Schema for health check response."""
    
    status: str
    timestamp: datetime
    version: str


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    
    success: bool = False
    error: dict
    timestamp: datetime