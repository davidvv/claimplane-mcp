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
    distance_km: Optional[float] = Field(None, ge=0, description="Great circle distance in km (if known from API)")

    class Config:
        json_schema_extra = {
            "example": {
                "departure_airport": "MAD",
                "arrival_airport": "JFK",
                "delay_hours": 5.0,
                "incident_type": "delay",
                "distance_km": 5780.42
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

    Calculates compensation based on flight distance, delay duration, and incident type.
    Uses EU261/2004 regulations for compensation calculation.

    Args:
        request: Flight details for eligibility check

    Returns:
        Eligibility result with calculated compensation amount
    """
    # Calculate compensation using the compensation service
    try:
        result = await CompensationService.calculate_compensation(
            departure_airport=request.departure_airport.upper(),
            arrival_airport=request.arrival_airport.upper(),
            delay_hours=request.delay_hours,
            incident_type=request.incident_type,
            distance_km=request.distance_km,  # Use API-provided distance if available
            use_api=True  # Enable AeroDataBox API for any airport
        )

        # Return the calculated result
        return EligibilityResponseSchema(
            eligible=result["eligible"],
            amount=result["amount"],
            distance_km=result["distance_km"],
            reason=result["reason"],
            requires_manual_review=result["requires_manual_review"]
        )
    except Exception as e:
        # If calculation fails (e.g., airport not found), return for manual review
        return EligibilityResponseSchema(
            eligible=True,
            amount=Decimal("0"),
            distance_km=request.distance_km or 0,
            reason="Unable to automatically calculate compensation. Your claim will be reviewed by our team to assess eligibility based on EU261/2004 regulations.",
            requires_manual_review=True
        )
