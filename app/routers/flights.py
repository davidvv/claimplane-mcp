"""Flight lookup endpoints with AeroDataBox API integration."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ValidationError
import logging

from app.database import get_db
from app.config import config
from app.schemas.flight_schemas import (
    AirportSearchRequestSchema,
    AirportSearchResponseSchema,
    RouteSearchRequestSchema,
    RouteSearchResponseSchema
)

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
                        f"API quota exceeded (>95%). Cannot retrieve data for {flight_number}"
                    )
                    return _get_no_data_response(flight_number, date, reason="quota_exceeded")

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
                    # Return no data available response
                    return _get_no_data_response(flight_number, date, reason="api_error")

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
            # Return no data available response
            return _get_no_data_response(flight_number, date, reason="error")

    else:
        # API disabled - return no data available
        logger.info(f"AeroDataBox API disabled. Cannot provide data for {flight_number}")
        return _get_no_data_response(flight_number, date, reason="api_disabled")


# Helper functions

def _get_no_data_response(flight_number: str, date: str, reason: str = "unavailable") -> dict:
    """
    Return a 'no data available' response when flight information cannot be retrieved.

    Instead of returning mock data, we acknowledge that real-time data is unavailable
    and inform the user that our team will manually process their claim.

    Args:
        flight_number: Flight number
        date: Flight date in YYYY-MM-DD format
        reason: Reason for unavailability (api_error, quota_exceeded, api_disabled, etc.)

    Returns:
        No data available response
    """
    reason_messages = {
        "api_error": "We're currently unable to retrieve real-time flight data due to a temporary API issue.",
        "quota_exceeded": "We've reached our daily limit for flight data requests.",
        "api_disabled": "Real-time flight data lookup is currently unavailable.",
        "unavailable": "We don't have real-time data available for this flight yet.",
        "error": "We encountered an issue retrieving flight data."
    }

    message = reason_messages.get(reason, reason_messages["unavailable"])

    return {
        "success": False,
        "error": "FLIGHT_DATA_UNAVAILABLE",
        "message": message,
        "userMessage": (
            f"We don't have real-time data for flight {flight_number.upper()} on {date} yet. "
            "Don't worry - you can still submit your claim and our team will verify the flight details manually."
        ),
        "flightNumber": flight_number.upper(),
        "date": date,
        "source": reason,
        "canProceedWithClaim": True,
        "manualReview": True
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

    # IMPORTANT: EU261 delay is measured to gate arrival (door opening), not runway touchdown
    # AeroDataBox does NOT provide gate arrival times, only runway touchdown
    # We must add estimated taxi time to get accurate EU261 delay calculations
    actual_arrival = None
    uses_runway_time = False
    if arrival:
        # Check for actual gate time (preferred but not provided by AeroDataBox)
        actual_arrival = arrival.get("actualTime", {}).get("utc") if isinstance(arrival.get("actualTime"), dict) else None

        if not actual_arrival:
            # Use runway touchdown time (AeroDataBox only provides this)
            actual_arrival = arrival.get("runwayTime", {}).get("utc") if isinstance(arrival.get("runwayTime"), dict) else None
            if actual_arrival:
                uses_runway_time = True

        if not actual_arrival:
            # Final fallback to revised/estimated time
            actual_arrival = arrival.get("revisedTime", {}).get("utc") if isinstance(arrival.get("revisedTime"), dict) else None

    # Calculate delay based on arrival times
    delay_minutes = None
    if scheduled_arrival and actual_arrival:
        try:
            scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
            actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
            delay_minutes = int((actual - scheduled).total_seconds() / 60)

            # Add airport-specific taxi time adjustment if using runway touchdown
            # EU261 measures delay to gate arrival (door opening), not runway touchdown
            # AeroDataBox only provides runway times, so we add taxi-in time
            if uses_runway_time and delay_minutes is not None:
                from app.services.airport_taxi_time_service import AirportTaxiTimeService

                # Get airport-specific taxi-in time (fallback to configured default)
                taxi_in_minutes = AirportTaxiTimeService.get_taxi_in_time(
                    arr_airport,
                    default=config.FLIGHT_TAXI_TIME_DEFAULT_MINUTES
                )

                # Convert float to int and add to delay
                taxi_in_adjustment = int(round(taxi_in_minutes))
                delay_minutes += taxi_in_adjustment

                logger.info(
                    f"Added {taxi_in_adjustment} min taxi-in time for {arr_airport} to {flight_number} "
                    f"(runway-only data, EU261 requires gate arrival)"
                )
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


# ============================================================================
# Phase 6.5: Flight Search by Route Endpoints
# ============================================================================


@router.get("/airports/search", response_model=AirportSearchResponseSchema)
async def search_airports(
    query: str = Query(..., min_length=2, max_length=50, description="Search query (IATA code, city, or airport name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
) -> AirportSearchResponseSchema:
    """
    Search airports by IATA code, name, or city.

    **Phase 6.5**: Airport autocomplete for route search feature.

    **Feature Flag**: Requires FLIGHT_SEARCH_ENABLED=true.

    Args:
        query: Search query (e.g., "munich", "MUC", "New York")
        limit: Maximum number of results (default: 10, max: 50)

    Returns:
        List of matching airports with IATA codes, names, cities, and countries

    Example Response:
        {
            "airports": [
                {
                    "iata": "MUC",
                    "icao": "EDDM",
                    "name": "Munich Airport",
                    "city": "Munich",
                    "country": "Germany"
                }
            ],
            "total": 1
        }

    Note:
        - Results are cached for 7 days
        - Searches by IATA code, airport name, or city name
        - Case-insensitive fuzzy matching
    """
    # Check feature flag
    if not config.FLIGHT_SEARCH_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Flight search is currently disabled. Please try again later or enter your flight number manually."
        )

    try:
        from app.services.flight_search_service import FlightSearchService

        # Validate input
        try:
            request_data = AirportSearchRequestSchema(query=query, limit=limit)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Airport search: query='{query}', limit={limit}")

        # Call service
        airports = await FlightSearchService.search_airports(
            query=request_data.query,
            limit=request_data.limit
        )

        # Format response
        response = AirportSearchResponseSchema(
            airports=airports,
            total=len(airports)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Airport search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Airport search temporarily unavailable. Please try again later."
        )


@router.get("/search", response_model=RouteSearchResponseSchema)
async def search_flights_by_route(
    from_: str = Query(..., alias="from", min_length=3, max_length=3, description="Departure airport IATA code"),
    to: str = Query(..., min_length=3, max_length=3, description="Arrival airport IATA code"),
    date: str = Query(..., description="Flight date in YYYY-MM-DD format"),
    time: Optional[str] = Query(None, description="Approximate time (morning/afternoon/evening or HH:MM)"),
    force_refresh: bool = Query(False, description="Force API call (bypasses cache)"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> RouteSearchResponseSchema:
    """
    Search for flights on a specific route and date.

    **Phase 6.5**: Route-based flight search for customers who don't know their flight number.

    **Feature Flag**: Requires FLIGHT_SEARCH_ENABLED=true.

    **8-Step Orchestration**:
    1. Validate inputs (IATA codes, date range)
    2. Check cache (24h TTL)
    3. Check quota availability (emergency brake at 95%)
    4. Call provider adapter (AeroDataBox)
    5. Track API usage
    6. Cache result
    7. Filter by time (if specified)
    8. Sort (delayed/cancelled first, then by departure time) and return

    Args:
        from_: Departure airport IATA code (e.g., "MUC")
        to: Arrival airport IATA code (e.g., "JFK")
        date: Flight date in YYYY-MM-DD format
        time: Optional time filter ("morning", "afternoon", "evening", or "HH:MM")
        force_refresh: Bypass cache and force API call (consumes 2 API credits)
        db: Database session for quota tracking and analytics

    Returns:
        List of matching flights with estimated EU261 compensation

    Example Response:
        {
            "flights": [
                {
                    "flightNumber": "LH8960",
                    "airline": "Lufthansa",
                    "airlineIata": "LH",
                    "departureAirport": "MUC",
                    "departureAirportName": "Munich Airport",
                    "arrivalAirport": "JFK",
                    "arrivalAirportName": "John F. Kennedy Intl",
                    "scheduledDeparture": "2025-01-15T13:45:00+01:00",
                    "scheduledArrival": "2025-01-15T17:20:00-05:00",
                    "actualDeparture": "2025-01-15T16:45:00+01:00",
                    "actualArrival": "2025-01-15T20:20:00-05:00",
                    "status": "delayed",
                    "delayMinutes": 180,
                    "distanceKm": 6200.0,
                    "estimatedCompensation": 600
                }
            ],
            "total": 1,
            "cached": false,
            "apiCreditsUsed": 2
        }

    Notes:
        - Results are cached for 24 hours (configurable)
        - Delayed/cancelled flights are prioritized in results
        - Estimated compensation is calculated based on EU261/2004 rules
        - Time filter is optional for better flexibility
        - Quota tracking shares Phase 6 quota (95% emergency brake)
    """
    # Check feature flag
    if not config.FLIGHT_SEARCH_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Flight search is currently disabled. Please try again later or enter your flight number manually."
        )

    try:
        from app.services.flight_search_service import FlightSearchService

        # Validate input
        try:
            request_data = RouteSearchRequestSchema(
                departure_iata=from_,
                arrival_iata=to,
                flight_date=date,
                approximate_time=time
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Extract user ID from headers (Phase 3 will use JWT)
        user_id_header = request.headers.get("X-Customer-ID") if request else None
        user_id = None
        if user_id_header:
            try:
                user_id = UUID(user_id_header)
            except ValueError:
                pass  # Invalid UUID, continue without user tracking

        logger.info(
            f"Route search: {request_data.departure_iata} → {request_data.arrival_iata} "
            f"on {request_data.flight_date} (time: {request_data.approximate_time or 'any'}, "
            f"user: {user_id}, force_refresh: {force_refresh})"
        )

        # Call service
        result = await FlightSearchService.search_flights_by_route(
            session=db,
            departure_iata=request_data.departure_iata,
            arrival_iata=request_data.arrival_iata,
            flight_date=request_data.flight_date,
            approximate_time=request_data.approximate_time,
            user_id=user_id,
            force_refresh=force_refresh
        )

        # Format response
        response = RouteSearchResponseSchema(
            flights=result.get("flights", []),
            total=result.get("total", 0),
            cached=result.get("cached", False),
            apiCreditsUsed=result.get("apiCreditsUsed", 0)
        )

        await db.commit()  # Commit quota tracking and analytics

        return response

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Route search error: {str(e)}", exc_info=True)
        # Return empty result with error message (graceful degradation)
        return RouteSearchResponseSchema(
            flights=[],
            total=0,
            cached=False,
            apiCreditsUsed=0
        )
