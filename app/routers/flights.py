"""Flight lookup endpoints - mock data for testing."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/flights", tags=["flights"])


class FlightStatusResponse(BaseModel):
    """Flight status response."""
    flightNumber: str
    airline: str
    departureAirport: str
    arrivalAirport: str
    departureDate: str
    scheduledDeparture: str
    actualDeparture: Optional[str] = None
    scheduledArrival: str
    actualArrival: Optional[str] = None
    status: str
    delay: Optional[int] = None  # minutes

    class Config:
        json_schema_extra = {
            "example": {
                "flightNumber": "BA123",
                "airline": "British Airways",
                "departureAirport": "LHR",
                "arrivalAirport": "JFK",
                "departureDate": "2024-01-15",
                "scheduledDeparture": "2024-01-15T10:00:00Z",
                "actualDeparture": "2024-01-15T14:30:00Z",
                "scheduledArrival": "2024-01-15T18:00:00Z",
                "actualArrival": "2024-01-15T22:30:00Z",
                "status": "delayed",
                "delay": 270
            }
        }


@router.get("/status/{flight_number}")
async def get_flight_status(
    flight_number: str,
    date: str = Query(..., description="Flight date in YYYY-MM-DD format"),
    refresh: bool = Query(False, description="Force refresh from external API")
) -> dict:
    """
    Get flight status (MOCK DATA FOR TESTING).

    This endpoint returns mock flight data for any flight number.
    In production, this would integrate with real flight tracking APIs.

    Args:
        flight_number: Flight number (e.g., BA123)
        date: Flight date in YYYY-MM-DD format
        refresh: Force refresh (ignored in mock)

    Returns:
        Flight status information
    """
    # Parse flight number to extract airline code
    import re
    match = re.match(r'([A-Z]{2,3})(\d+)', flight_number.upper())

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Invalid flight number format. Expected format: AA123 or AAA123"
        )

    airline_code = match.group(1)
    flight_num = match.group(2)

    # Mock airline mapping
    airlines = {
        "BA": "British Airways",
        "AA": "American Airlines",
        "DL": "Delta Air Lines",
        "UA": "United Airlines",
        "LH": "Lufthansa",
        "AF": "Air France",
        "KL": "KLM",
        "IB": "Iberia",
        "VY": "Vueling",
        "FR": "Ryanair",
        "U2": "easyJet",
        "EZY": "easyJet",
        "W6": "Wizz Air",
    }

    airline_name = airlines.get(airline_code, f"{airline_code} Airlines")

    # Mock flight data - always returns a delayed flight for testing compensation
    flight_data = FlightStatusResponse(
        flightNumber=flight_number.upper(),
        airline=airline_name,
        departureAirport="MAD",  # Madrid
        arrivalAirport="JFK",    # New York JFK
        departureDate=date,
        scheduledDeparture=f"{date}T10:00:00Z",
        actualDeparture=f"{date}T14:30:00Z",  # 4.5 hours delayed
        scheduledArrival=f"{date}T18:00:00Z",
        actualArrival=f"{date}T22:30:00Z",
        status="delayed",
        delay=270  # 4.5 hours = 270 minutes
    )

    return {
        "success": True,
        "data": flight_data.dict()
    }
