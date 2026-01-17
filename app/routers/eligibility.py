"""Eligibility check endpoints - public access."""
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from decimal import Decimal

from app.services.compensation_service import CompensationService

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


class FlightLegInput(BaseModel):
    """Schema for a single flight leg in a multi-leg journey."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    flight_number: Optional[str] = Field(None, description="Flight number")


class EligibilityRequestSchema(BaseModel):
    """Request schema for eligibility check."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA code")
    delay_hours: Optional[float] = Field(None, le=72, description="Delay in hours (negative = early arrival)")
    incident_type: str = Field(..., description="delay, cancellation, denied_boarding, baggage_delay")
    distance_km: Optional[float] = Field(None, ge=0, description="Great circle distance in km (if known from API)")
    flights: Optional[List[FlightLegInput]] = Field(None, description="List of flight legs for connecting flights")

    class Config:
        json_schema_extra = {
            "example": {
                "departure_airport": "MAD",
                "arrival_airport": "JFK",
                "delay_hours": 5.0,
                "incident_type": "delay",
                "distance_km": 5780.42,
                "flights": [
                    {"departure_airport": "MAD", "arrival_airport": "LHR", "flight_number": "IB3166"},
                    {"departure_airport": "LHR", "arrival_airport": "JFK", "flight_number": "BA173"}
                ]
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
        # Determine airports for distance calculation
        # If flights list is provided (multi-leg), use Origin of first and Destination of last
        departure_iata = request.departure_airport.upper()
        arrival_iata = request.arrival_airport.upper()
        distance_to_use = request.distance_km
        
        if request.flights and len(request.flights) > 0:
            departure_iata = request.flights[0].departure_airport.upper()
            arrival_iata = request.flights[-1].arrival_airport.upper()
            # Force recalculation of distance for multi-leg to ensure Great Circle rule (Origin -> Final)
            # as frontend might have calculated sum of legs or single leg distance
            distance_to_use = None
            
        result = await CompensationService.calculate_compensation(
            departure_airport=departure_iata,
            arrival_airport=arrival_iata,
            delay_hours=request.delay_hours,
            incident_type=request.incident_type,
            distance_km=distance_to_use,  # Use API-provided distance if available
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
