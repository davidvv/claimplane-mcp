"""Eligibility check endpoints - public access."""
from typing import Optional, List
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from decimal import Decimal

from app.services.compensation_service import CompensationService
from app.dependencies.rate_limit import limiter

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


class FlightLegInput(BaseModel):
    """Schema for a single flight leg in a multi-leg journey."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA code", alias="departureAirport")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA code", alias="arrivalAirport")
    flight_number: Optional[str] = Field(None, description="Flight number", alias="flightNumber")
    
    class Config:
        populate_by_name = True


class EligibilityRequestSchema(BaseModel):
    """Request schema for eligibility check."""
    departure_airport: str = Field(..., min_length=3, max_length=3, description="IATA code", alias="departureAirport")
    arrival_airport: str = Field(..., min_length=3, max_length=3, description="IATA code", alias="arrivalAirport")
    delay_hours: Optional[float] = Field(None, le=72, description="Delay in hours (negative = early arrival)", alias="delayHours")
    incident_type: str = Field(..., description="delay, cancellation, denied_boarding, baggage_delay", alias="incidentType")
    distance_km: Optional[float] = Field(None, ge=0, description="Great circle distance in km (if known from API)", alias="distanceKm")
    flights: Optional[List[FlightLegInput]] = Field(None, description="List of flight legs for connecting flights")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "departureAirport": "MAD",
                "arrivalAirport": "JFK",
                "delayHours": 5.0,
                "incidentType": "delay",
                "distanceKm": 5780.42,
                "flights": [
                    {"departureAirport": "MAD", "arrivalAirport": "LHR", "flightNumber": "IB3166"},
                    {"departureAirport": "LHR", "arrivalAirport": "JFK", "flightNumber": "BA173"}
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
@limiter.limit("20/minute")
async def check_eligibility(request: Request, response: Response, data: EligibilityRequestSchema) -> EligibilityResponseSchema:
    """
    Check eligibility for flight compensation (PUBLIC ENDPOINT).

    Calculates compensation based on flight distance, delay duration, and incident type.
    Uses EU261/2004 regulations for compensation calculation.

    Args:
        request: FastAPI request object (for rate limiting)
        data: Flight details for eligibility check

    Returns:
        Eligibility result with calculated compensation amount
    """
    # Calculate compensation using the compensation service
    try:
        # Determine airports for distance calculation
        # If flights list is provided (multi-leg), use Origin of first and Destination of last
        departure_iata = data.departure_airport.upper()
        arrival_iata = data.arrival_airport.upper()
        distance_to_use = data.distance_km
        
        if data.flights and len(data.flights) > 0:
            departure_iata = data.flights[0].departure_airport.upper()
            arrival_iata = data.flights[-1].arrival_airport.upper()
            # Force recalculation of distance for multi-leg to ensure Great Circle rule (Origin -> Final)
            # as frontend might have calculated sum of legs or single leg distance
            distance_to_use = None
            
        result = await CompensationService.calculate_compensation(
            departure_airport=departure_iata,
            arrival_airport=arrival_iata,
            delay_hours=data.delay_hours,
            incident_type=data.incident_type,
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
            distance_km=data.distance_km or 0,
            reason="Unable to automatically calculate compensation. Your claim will be reviewed by our team to assess eligibility based on EU261/2004 regulations.",
            requires_manual_review=True
        )
