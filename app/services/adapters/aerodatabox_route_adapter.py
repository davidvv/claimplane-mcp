"""AeroDataBox implementation of flight search adapter.

This adapter uses the AeroDataBox API to search flights by route and airports.
Reuses the existing AeroDataBoxService HTTP client for consistency with Phase 6.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx

from app.config import config
from app.services.adapters.flight_search_adapter import FlightSearchAdapter
from app.services.aerodatabox_service import AeroDataBoxService
from app.exceptions import (
    AeroDataBoxError,
    AeroDataBoxFlightNotFoundError,
    AeroDataBoxPermanentError
)

logger = logging.getLogger(__name__)


class AeroDataBoxRouteAdapter(FlightSearchAdapter):
    """AeroDataBox implementation for route search.

    Uses Phase 6's AeroDataBox service for consistent HTTP client behavior.
    Endpoint: GET /flights/{departure}/{arrival}/{date}
    Tier: TIER_2 (2 credits per call)
    """

    def __init__(self):
        """Initialize AeroDataBox route adapter."""
        self.service = AeroDataBoxService()
        self.base_url = config.FLIGHT_SEARCH_BASE_URL or config.AERODATABOX_BASE_URL
        self.api_key = config.FLIGHT_SEARCH_API_KEY or config.AERODATABOX_API_KEY

    async def search_route(
        self,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str
    ) -> List[Dict[str, Any]]:
        """Search for all flights on a specific route and date.

        Args:
            departure_iata: Departure airport IATA code (e.g., "MUC")
            arrival_iata: Arrival airport IATA code (e.g., "JFK")
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            List of flight dictionaries in standardized format

        Raises:
            AeroDataBoxError: If API call fails
        """
        # Normalize inputs
        departure_iata = departure_iata.upper()
        arrival_iata = arrival_iata.upper()

        # Construct API endpoint
        # AeroDataBox route endpoint: /flights/{from}/{to}/{date}
        endpoint = f"/flights/{departure_iata}/{arrival_iata}/{flight_date}"

        logger.info(f"Searching route {departure_iata} → {arrival_iata} on {flight_date}")

        try:
            # Call API using aerodatabox_service's retry logic
            response = await self.service._retry_with_backoff(
                self._make_api_call,
                endpoint
            )

            # Parse and standardize response
            flights = self._parse_route_response(response)

            logger.info(f"Found {len(flights)} flights on route {departure_iata} → {arrival_iata}")
            return flights

        except AeroDataBoxFlightNotFoundError:
            # No flights found on this route - return empty list (not an error)
            logger.info(f"No flights found on route {departure_iata} → {arrival_iata} on {flight_date}")
            return []
        except AeroDataBoxError as e:
            # Log error and return empty list - no mock data
            logger.error(f"AeroDataBox route search failed ({str(e)}). Returning empty results.")
            return []

    async def search_airports(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search airports by IATA code, name, or city.

        Uses static airport database for fast fuzzy search.
        Supports search by IATA code, city name, or airport name.

        Args:
            query: Search query (e.g., "munich", "MUC", "New York")
            limit: Maximum number of results to return

        Returns:
            List of airport dictionaries

        Raises:
            AeroDataBoxError: If search fails
        """
        try:
            from app.services.airport_database_service import AirportDatabaseService

            # Use static airport database for fuzzy search
            airports = AirportDatabaseService.search(query, limit)

            logger.info(f"Airport search for '{query}': found {len(airports)} results")
            return airports

        except Exception as e:
            logger.error(f"Airport search error: {str(e)}", exc_info=True)
            return []

    async def _make_api_call(self, endpoint: str) -> Dict[str, Any]:
        """Make HTTP request to AeroDataBox API.

        Args:
            endpoint: API endpoint (e.g., "/flights/MUC/JFK/2025-01-15")

        Returns:
            API response as dictionary

        Raises:
            AeroDataBoxError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.service._get_headers()

        async with httpx.AsyncClient(timeout=self.service.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Handle specific status codes
                if e.response.status_code == 404:
                    raise AeroDataBoxFlightNotFoundError(
                        message="No flights found on this route",
                        details={"endpoint": endpoint, "status_code": 404}
                    )
                elif e.response.status_code in (401, 403):
                    raise AeroDataBoxPermanentError(
                        message="Authentication failed",
                        details={"endpoint": endpoint, "status_code": e.response.status_code}
                    )
                else:
                    raise AeroDataBoxError(
                        message=f"API request failed: {str(e)}",
                        error_code=f"HTTP_{e.response.status_code}",
                        status_code=e.response.status_code,
                        retryable=e.response.status_code >= 500
                    )

    def _parse_route_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AeroDataBox route search response to standardized format.

        Args:
            response: Raw API response

        Returns:
            List of standardized flight dictionaries
        """
        flights = []

        # AeroDataBox returns a list of flights
        flight_list = response if isinstance(response, list) else [response]

        for flight_data in flight_list:
            try:
                # Extract flight info
                flight_number = flight_data.get("number", "")

                # Airline info
                airline = flight_data.get("airline", {})
                airline_name = airline.get("name") if airline else None
                airline_iata = airline.get("iata") if airline else None

                # Departure info
                departure = flight_data.get("departure", {})
                dep_airport = departure.get("airport", {}) if departure else {}
                dep_airport_iata = dep_airport.get("iata") if dep_airport else None
                dep_airport_name = dep_airport.get("name") if dep_airport else None

                # Arrival info
                arrival = flight_data.get("arrival", {})
                arr_airport = arrival.get("airport", {}) if arrival else {}
                arr_airport_iata = arr_airport.get("iata") if arr_airport else None
                arr_airport_name = arr_airport.get("name") if arr_airport else None

                # Scheduled times
                scheduled_departure = departure.get("scheduledTime", {}).get("utc") if departure else None
                scheduled_arrival = arrival.get("scheduledTime", {}).get("utc") if arrival else None

                # Actual times
                actual_departure = departure.get("actualTime", {}).get("utc") if departure else None
                actual_arrival = arrival.get("actualTime", {}).get("utc") if arrival else None

                # Status
                status = flight_data.get("status", "scheduled")

                # Calculate delay
                delay_minutes = None
                if scheduled_arrival and actual_arrival:
                    try:
                        scheduled_dt = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
                        actual_dt = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
                        delay_minutes = int((actual_dt - scheduled_dt).total_seconds() / 60)
                    except (ValueError, AttributeError):
                        pass

                # CRITICAL: Check if flight is in the future
                # Future flights cannot have actual times or delays
                if scheduled_departure:
                    try:
                        scheduled_dep_dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                        current_time = datetime.now(scheduled_dep_dt.tzinfo)

                        if scheduled_dep_dt > current_time:
                            # Override for future flights
                            status = "scheduled"
                            actual_departure = None
                            actual_arrival = None
                            delay_minutes = None
                    except (ValueError, AttributeError):
                        pass

                # Distance (if available)
                distance_km = flight_data.get("greatCircleDistance", {}).get("km")

                # Build standardized flight object
                standardized_flight = {
                    "flightNumber": flight_number,
                    "airline": airline_name,
                    "airlineIata": airline_iata,
                    "departureAirport": dep_airport_iata,
                    "departureAirportName": dep_airport_name,
                    "arrivalAirport": arr_airport_iata,
                    "arrivalAirportName": arr_airport_name,
                    "scheduledDeparture": scheduled_departure,
                    "scheduledArrival": scheduled_arrival,
                    "actualDeparture": actual_departure,
                    "actualArrival": actual_arrival,
                    "status": status,
                    "delayMinutes": delay_minutes,
                    "distanceKm": distance_km,
                }

                flights.append(standardized_flight)

            except Exception as e:
                logger.warning(f"Error parsing flight data: {str(e)}")
                continue

        return flights

    async def _get_airport_info(self, iata_code: str) -> Optional[Dict[str, Any]]:
        """Get airport information by IATA code.

        Args:
            iata_code: 3-letter IATA code

        Returns:
            Airport info dictionary or None

        Raises:
            AeroDataBoxError: If API call fails
        """
        endpoint = f"/airports/iata/{iata_code}"

        try:
            response = await self._make_api_call(endpoint)

            # Parse response
            if response:
                return {
                    "iata": response.get("iata", iata_code),
                    "icao": response.get("icao"),
                    "name": response.get("name", ""),
                    "city": response.get("municipalityName", ""),
                    "country": response.get("countryCode", "")
                }
        except AeroDataBoxFlightNotFoundError:
            return None
        except AeroDataBoxError:
            return None

        return None
