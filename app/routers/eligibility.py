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

    Currently accepts all claims for manual review by admin team.
    Automatic eligibility calculation will be implemented later.

    Args:
        request: Flight details for eligibility check

    Returns:
        Eligibility result indicating manual review is required
    """
    # For now, accept all claims for manual review
    # TODO: Implement automatic eligibility calculation when we have:
    # - Real-time flight data API integration
    # - Complete airport database
    # - EU261 rule engine

    # Try to estimate distance for display purposes only
    try:
        result = CompensationService.calculate_compensation(
            departure_airport=request.departure_airport.upper(),
            arrival_airport=request.arrival_airport.upper(),
            delay_hours=request.delay_hours,
            incident_type=request.incident_type
        )
        distance = result.get("distance_km", 0)
    except Exception:
        distance = 0

    # Return positive response that requires manual review
    return EligibilityResponseSchema(
        eligible=True,
        amount=Decimal("0"),  # Amount to be determined by admin
        distance_km=distance,
        reason="Your claim will be reviewed by our team. We'll assess your eligibility based on EU261/2004 regulations and notify you of the outcome.",
        requires_manual_review=True
    )
