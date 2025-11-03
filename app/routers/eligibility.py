"""Eligibility check endpoints - public access."""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from decimal import Decimal

from app.services.compensation_service import CompensationService

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


class EligibilityRequestSchema(BaseModel):
    """Request schema for eligibility check."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    delay_hours: Optional[float] = Field(None, ge=0, le=72, description="Delay in hours")
    incident_type: str = Field(..., description="delay, cancellation, denied_boarding, baggage_delay")

    class Config:
        json_schema_extra = {
            "example": {
                "departure_airport": "MAD",
                "arrival_airport": "JFK",
                "delay_hours": 5.0,
                "incident_type": "delay"
            }
        }


class EligibilityResponseSchema(BaseModel):
    """Response schema for eligibility check."""
    eligible: bool
    amount: Decimal
    distance_km: float
    reason: str
    requires_manual_review: bool

    class Config:
        json_schema_extra = {
            "example": {
                "eligible": True,
                "amount": 600,
                "distance_km": 5780.42,
                "reason": "Flight qualifies for compensation under EU261/2004",
                "requires_manual_review": False
            }
        }


@router.post("/check", response_model=EligibilityResponseSchema)
async def check_eligibility(request: EligibilityRequestSchema) -> EligibilityResponseSchema:
    """
    Check eligibility for flight compensation (PUBLIC ENDPOINT).

    This endpoint does not require authentication and returns only
    eligibility information based on flight details.

    Args:
        request: Flight details for eligibility check

    Returns:
        Eligibility result with compensation amount and reasons
    """
    # Call existing compensation service
    result = CompensationService.calculate_compensation(
        departure_airport=request.departure_airport.upper(),
        arrival_airport=request.arrival_airport.upper(),
        delay_hours=request.delay_hours,
        incident_type=request.incident_type
    )

    return EligibilityResponseSchema(**result)
