"""SQLAlchemy models for the flight claim system."""
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base


class Customer(Base):
    """Customer model representing a user who can submit claims."""
    
    __tablename__ = "customers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"
    
    @validates('email')
    def validate_email(self, key, address):
        """Validate email format."""
        if address:
            # Basic email validation - in a real app, use email-validator library
            if '@' not in address or '.' not in address.split('@')[-1]:
                raise ValueError("Invalid email format")
        return address
    
    @hybrid_property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def address(self):
        """Return address as a nested object."""
        # Check if any address field has a non-None value
        if (self.street is not None or
            self.city is not None or
            self.postal_code is not None or
            self.country is not None):

            return {
                "street": self.street or None,
                "city": self.city or None,
                "postalCode": self.postal_code or None,
                "country": self.country or None
            }
        return None


class Claim(Base):
    """Claim model representing a flight compensation claim."""
    
    __tablename__ = "claims"
    
    # Incident types
    INCIDENT_DELAY = "delay"
    INCIDENT_CANCELLATION = "cancellation"
    INCIDENT_DENIED_BOARDING = "denied_boarding"
    INCIDENT_BAGGAGE_DELAY = "baggage_delay"
    
    INCIDENT_TYPES = [
        INCIDENT_DELAY,
        INCIDENT_CANCELLATION,
        INCIDENT_DENIED_BOARDING,
        INCIDENT_BAGGAGE_DELAY
    ]
    
    # Status types
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PAID = "paid"
    STATUS_CLOSED = "closed"
    
    STATUS_TYPES = [
        STATUS_DRAFT,
        STATUS_SUBMITTED,
        STATUS_UNDER_REVIEW,
        STATUS_APPROVED,
        STATUS_REJECTED,
        STATUS_PAID,
        STATUS_CLOSED
    ]
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    flight_number = Column(String(10), nullable=False)
    airline = Column(String(100), nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_airport = Column(String(3), nullable=False)  # IATA code
    arrival_airport = Column(String(3), nullable=False)  # IATA code
    incident_type = Column(String(50), nullable=False)
    status = Column(String(50), default=STATUS_SUBMITTED)
    compensation_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="claims")
    
    def __repr__(self):
        return f"<Claim(id={self.id}, flight={self.flight_number}, incident={self.incident_type}, status={self.status})>"
    
    @validates('incident_type')
    def validate_incident_type(self, key, incident_type):
        """Validate incident type."""
        if incident_type not in self.INCIDENT_TYPES:
            raise ValueError(f"Invalid incident type. Must be one of: {', '.join(self.INCIDENT_TYPES)}")
        return incident_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status."""
        if status not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.STATUS_TYPES)}")
        return status
    
    @validates('departure_airport', 'arrival_airport')
    def validate_airport_code(self, key, code):
        """Validate IATA airport codes (should be 3 characters)."""
        if code and len(code) != 3:
            raise ValueError("Airport code must be 3 characters")
        return code.upper()
    
    @validates('flight_number')
    def validate_flight_number(self, key, flight_number):
        """Validate flight number format."""
        if flight_number:
            # Basic validation - should contain airline code and number
            if not any(char.isdigit() for char in flight_number):
                raise ValueError("Flight number must contain digits")
            if len(flight_number) < 3:
                raise ValueError("Flight number too short")
        return flight_number.upper()