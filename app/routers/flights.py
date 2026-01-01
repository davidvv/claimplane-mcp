"""Flight lookup endpoints with AeroDataBox API integration."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.config import config

logger = logging.getLogger(__name__)

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
    refresh: bool = Query(False, description="Force refresh from cache (bypasses cache)"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get flight status from AeroDataBox API (or mock data if API disabled).

    **Phase 6 Integration**: This endpoint now uses the real AeroDataBox API
    when AERODATABOX_ENABLED=true. It includes:
    - 24-hour Redis caching (unless refresh=True)
    - Quota tracking and monitoring
    - Graceful fallback to mock data if API unavailable

    **Feature Flag**: Set AERODATABOX_ENABLED=true to use real API data.

    Args:
        flight_number: Flight number (e.g., BA123)
        date: Flight date in YYYY-MM-DD format
        refresh: Force API call (bypasses cache, consumes 2 API credits)
        db: Database session for quota tracking

    Returns:
        Flight status information with API source indicator

    Example Response:
        {
            "success": true,
            "data": {
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
            },
            "source": "aerodatabox",  # or "cached" or "mock"
            "cached": false,
            "apiCreditsUsed": 2
        }
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Expected YYYY-MM-DD"
        )

    # Normalize flight number
    flight_number = flight_number.upper().replace(" ", "")

    # Check if API is enabled (Phase 6 feature flag)
    if config.AERODATABOX_ENABLED:
        try:
            from app.services.aerodatabox_service import aerodatabox_service
            from app.services.cache_service import CacheService
            from app.services.quota_tracking_service import QuotaTrackingService

            logger.info(
                f"Fetching flight status for {flight_number} on {date} "
                f"(refresh={refresh}, API enabled)"
            )

            api_credits_used = 0
            source = "unknown"
            cached = False

            # Step 1: Check cache (unless refresh=True)
            flight_data_dict = None
            if not refresh:
                cached_flight = await CacheService.get_cached_flight(flight_number, date)
                if cached_flight:
                    logger.info(f"Using cached flight data for {flight_number}")
                    flight_data_dict = cached_flight.get("data")
                    cached = True
                    source = "cached"

            # Step 2: If no cache, call API
            if flight_data_dict is None:
                # Check quota availability
                quota_available = await QuotaTrackingService.check_quota_available(db)

                if not quota_available:
                    logger.warning(
                        f"API quota exceeded (>95%). Falling back to mock data for {flight_number}"
                    )
                    return _get_mock_flight_status(flight_number, date, source="quota_exceeded")

                # Call AeroDataBox API
                start_time = datetime.now()

                try:
                    flight_data_dict = await aerodatabox_service.get_flight_status(
                        flight_number, date
                    )

                    # Calculate response time
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                    # Track API call
                    await QuotaTrackingService.track_api_call(
                        session=db,
                        endpoint=f"/flights/number/{flight_number}/{date}",
                        tier_level="TIER_2",
                        credits_used=2,
                        http_status=200,
                        response_time_ms=response_time_ms,
                        triggered_by_user_id=None,  # Public endpoint
                        claim_id=None
                    )

                    api_credits_used = 2
                    source = "aerodatabox"

                    # Cache the result
                    await CacheService.cache_flight(
                        flight_number,
                        date,
                        flight_data_dict,
                        ttl=config.FLIGHT_CACHE_TTL_SECONDS
                    )

                    logger.info(f"Successfully retrieved flight data from AeroDataBox API")

                except Exception as e:
                    # Track failed API call
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                    await QuotaTrackingService.track_api_call(
                        session=db,
                        endpoint=f"/flights/number/{flight_number}/{date}",
                        tier_level="TIER_2",
                        credits_used=0,  # No credits charged on error
                        http_status=getattr(e, 'status_code', None),
                        response_time_ms=response_time_ms,
                        error_message=str(e),
                        triggered_by_user_id=None,
                        claim_id=None
                    )

                    logger.error(f"AeroDataBox API error: {str(e)}")
                    # Fall back to mock data
                    return _get_mock_flight_status(flight_number, date, source="api_error")

            # Step 3: Parse API response
            flight_parsed = _parse_aerodatabox_response(flight_data_dict, flight_number, date)

            # Add metadata
            response = {
                "success": True,
                "data": flight_parsed.dict(),
                "source": source,
                "cached": cached,
                "apiCreditsUsed": api_credits_used
            }

            await db.commit()  # Commit quota tracking

            return response

        except Exception as e:
            logger.error(
                f"Unexpected error in flight status lookup: {str(e)}",
                exc_info=True
            )
            # Fall back to mock data on any error
            return _get_mock_flight_status(flight_number, date, source="error")

    else:
        # API disabled - return mock data
        logger.info(f"AeroDataBox API disabled. Returning mock data for {flight_number}")
        return _get_mock_flight_status(flight_number, date, source="mock")


# Helper functions

def _get_mock_flight_status(flight_number: str, date: str, source: str = "mock") -> dict:
    """
    Generate mock flight status data for testing or fallback.

    Args:
        flight_number: Flight number
        date: Flight date in YYYY-MM-DD format
        source: Source indicator (mock, api_error, quota_exceeded, etc.)

    Returns:
        Mock flight status response
    """
    import re

    # Parse flight number to extract airline code
    match = re.match(r'([A-Z]{2,3})(\d+)', flight_number.upper())

    if match:
        airline_code = match.group(1)

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
    else:
        airline_name = "Mock Airlines"

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
        "data": flight_data.dict(),
        "source": source,
        "cached": False,
        "apiCreditsUsed": 0
    }


def _parse_aerodatabox_response(api_response: dict, flight_number: str, date: str) -> FlightStatusResponse:
    """
    Parse AeroDataBox API response into FlightStatusResponse format.

    Args:
        api_response: Raw API response from AeroDataBox
        flight_number: Flight number
        date: Flight date

    Returns:
        FlightStatusResponse object
    """
    # Handle both single flight and list response
    if isinstance(api_response, list) and len(api_response) > 0:
        flight = api_response[0]
    elif isinstance(api_response, dict):
        flight = api_response
    else:
        # Unexpected format - return minimal data
        return FlightStatusResponse(
            flightNumber=flight_number,
            airline="Unknown",
            departureAirport="",
            arrivalAirport="",
            departureDate=date,
            scheduledDeparture=f"{date}T00:00:00Z",
            scheduledArrival=f"{date}T00:00:00Z",
            status="unknown"
        )

    # Extract airline info
    airline = flight.get("airline", {})
    airline_name = airline.get("name") if airline else "Unknown"

    # Extract departure info
    departure = flight.get("departure", {})
    dep_airport = departure.get("airport", {}).get("iata") if departure else ""
    scheduled_departure = departure.get("scheduledTime", {}).get("utc") if departure else None
    actual_departure = departure.get("actualTime", {}).get("utc") if departure else None

    # Extract arrival info
    arrival = flight.get("arrival", {})
    arr_airport = arrival.get("airport", {}).get("iata") if arrival else ""
    scheduled_arrival = arrival.get("scheduledTime", {}).get("utc") if arrival else None
    actual_arrival = arrival.get("actualTime", {}).get("utc") if arrival else None

    # Calculate delay
    delay_minutes = None
    if scheduled_arrival and actual_arrival:
        try:
            scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
            actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
            delay_minutes = int((actual - scheduled).total_seconds() / 60)
        except Exception:
            pass

    # Flight status
    status = flight.get("status", "scheduled")

    return FlightStatusResponse(
        flightNumber=flight_number,
        airline=airline_name,
        departureAirport=dep_airport or "",
        arrivalAirport=arr_airport or "",
        departureDate=date,
        scheduledDeparture=scheduled_departure or f"{date}T00:00:00Z",
        actualDeparture=actual_departure,
        scheduledArrival=scheduled_arrival or f"{date}T00:00:00Z",
        actualArrival=actual_arrival,
        status=status,
        delay=delay_minutes
    )
