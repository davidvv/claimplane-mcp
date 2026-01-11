"""AeroDataBox API client service with retry logic and error handling.

This service provides HTTP client for AeroDataBox API with:
- Exponential backoff retry logic
- Error classification (retryable vs permanent)
- Flight status, airport info, and distance calculation
- Comprehensive error handling
"""
import asyncio
import logging
import random
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2

import httpx
from httpx import ConnectError, TimeoutException, NetworkError, HTTPStatusError

from app.config import config
from app.exceptions import (
    AeroDataBoxError,
    AeroDataBoxRetryableError,
    AeroDataBoxPermanentError,
    AeroDataBoxNetworkError,
    AeroDataBoxTimeoutError,
    AeroDataBoxAuthenticationError,
    AeroDataBoxFlightNotFoundError,
    AeroDataBoxQuotaExceededError,
    AeroDataBoxRateLimitError,
    AeroDataBoxServerError,
    AeroDataBoxClientError
)

logger = logging.getLogger(__name__)


class AeroDataBoxService:
    """
    HTTP client for AeroDataBox Flight Status API.

    Features:
    - Automatic retry with exponential backoff
    - Error classification and handling
    - Flight status and airport information endpoints
    - Distance calculation between airports
    """

    def __init__(self, max_retries: int = None, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize AeroDataBox service.

        Args:
            max_retries: Maximum number of retry attempts (default from config)
            base_delay: Base delay for exponential backoff in seconds
            max_delay: Maximum delay between retries in seconds
        """
        self.base_url = config.AERODATABOX_BASE_URL
        self.api_key = config.AERODATABOX_API_KEY
        self.timeout = config.AERODATABOX_TIMEOUT
        self.max_retries = max_retries or config.AERODATABOX_MAX_RETRIES
        self.base_delay = base_delay
        self.max_delay = max_delay

        # Validate configuration
        if not self.api_key:
            logger.warning("AERODATABOX_API_KEY not configured. API calls will fail.")

        if not config.AERODATABOX_ENABLED:
            logger.info("AeroDataBox API is disabled (AERODATABOX_ENABLED=false)")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Headers dictionary with API key
        """
        # Check if using RapidAPI (base URL contains rapidapi.com)
        if "rapidapi.com" in self.base_url.lower():
            return {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
                "Accept": "application/json",
                "User-Agent": f"ClaimPlane/{config.API_VERSION}"
            }
        # Check if using API.Market (base URL contains api.market)
        elif "api.market" in self.base_url.lower():
            return {
                "x-api-market-key": self.api_key,
                "accept": "application/json",
                "User-Agent": f"ClaimPlane/{config.API_VERSION}"
            }
        else:
            # Direct AeroDataBox API
            return {
                "X-API-Key": self.api_key,
                "Accept": "application/json",
                "User-Agent": f"ClaimPlane/{config.API_VERSION}"
            }

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = self.base_delay * (2 ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter (±25% randomization to prevent thundering herd)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter

        return max(0.1, delay)  # Minimum 0.1 seconds

    def _is_retryable_error(self, error: Exception) -> Tuple[bool, Optional[int]]:
        """
        Determine if an error is retryable and extract retry-after header.

        Args:
            error: Exception to classify

        Returns:
            Tuple of (is_retryable: bool, retry_after: Optional[int])
        """
        # Network errors are retryable
        if isinstance(error, (ConnectError, TimeoutException, NetworkError)):
            return True, None

        # HTTP status errors
        if isinstance(error, HTTPStatusError):
            response = error.response
            status_code = response.status_code

            # Extract Retry-After header if present
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass

            # 5xx server errors are retryable
            if 500 <= status_code < 600:
                return True, retry_after

            # 429 rate limit is retryable
            if status_code == 429:
                return True, retry_after

            # 4xx client errors are not retryable (except 429)
            return False, None

        # Unknown errors are not retryable
        return False, None

    def _classify_error(self, error: Exception, context: str = None,
                       operation: str = None, http_status: int = None,
                       response_text: str = None) -> AeroDataBoxError:
        """
        Classify exception into appropriate AeroDataBox error type.

        Args:
            error: Original exception
            context: Context description
            operation: Operation being performed
            http_status: HTTP status code (if applicable)
            response_text: Response body text (if applicable)

        Returns:
            Classified AeroDataBoxError
        """
        details = {
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Network errors
        if isinstance(error, TimeoutException):
            return AeroDataBoxTimeoutError(
                message=f"Request timed out after {self.timeout}s",
                timeout_seconds=self.timeout,
                context=context,
                details=details
            )

        if isinstance(error, (ConnectError, NetworkError)):
            return AeroDataBoxNetworkError(
                message=f"Network error: {str(error)}",
                original_error=error,
                context=context,
                details=details
            )

        # HTTP status errors
        if isinstance(error, HTTPStatusError):
            response = error.response
            status_code = response.status_code
            details["http_status"] = status_code
            details["response_text"] = response_text or response.text[:500]

            # Authentication errors (401, 403)
            if status_code in (401, 403):
                return AeroDataBoxAuthenticationError(
                    message=f"Authentication failed (HTTP {status_code})",
                    original_error=error,
                    context=context,
                    details=details
                )

            # Flight not found (404)
            if status_code == 404:
                return AeroDataBoxFlightNotFoundError(
                    message=f"Flight not found (HTTP {status_code})",
                    context=context,
                    details=details
                )

            # Rate limit (429)
            if status_code == 429:
                retry_after = None
                if "Retry-After" in response.headers:
                    try:
                        retry_after = int(response.headers["Retry-After"])
                    except ValueError:
                        pass

                return AeroDataBoxRateLimitError(
                    message=f"Rate limit exceeded (HTTP {status_code})",
                    retry_after=retry_after,
                    original_error=error,
                    context=context,
                    details=details
                )

            # Server errors (5xx)
            if 500 <= status_code < 600:
                return AeroDataBoxServerError(
                    message=f"Server error (HTTP {status_code})",
                    status_code=status_code,
                    original_error=error,
                    context=context,
                    details=details
                )

            # Client errors (4xx, excluding handled above)
            if 400 <= status_code < 500:
                return AeroDataBoxClientError(
                    message=f"Client error (HTTP {status_code})",
                    status_code=status_code,
                    original_error=error,
                    context=context,
                    details=details
                )

        # Generic error
        return AeroDataBoxError(
            message=f"Unexpected error: {str(error)}",
            error_code="AERO_UNKNOWN_ERROR",
            original_error=error,
            context=context,
            details=details
        )

    async def _retry_with_backoff(self, operation, *args, **kwargs):
        """
        Execute operation with retry logic and exponential backoff.

        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Operation result

        Raises:
            AeroDataBoxError: Classified error after all retries exhausted
        """
        last_exception = None
        operation_name = operation.__name__ if hasattr(operation, '__name__') else str(operation)

        for attempt in range(self.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded after {attempt} retries")
                return result

            except Exception as e:
                last_exception = e

                # Check if we've exhausted retries
                if attempt == self.max_retries:
                    logger.error(f"{operation_name} failed after {self.max_retries + 1} attempts: {str(e)}")
                    break

                # Check if error is retryable
                is_retryable, retry_after = self._is_retryable_error(e)

                if not is_retryable:
                    logger.error(f"{operation_name} failed with non-retryable error: {str(e)}")
                    break

                # Calculate delay
                if retry_after:
                    delay = retry_after
                    logger.info(f"{operation_name} retry after {delay}s (Retry-After header)")
                else:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.info(f"{operation_name} retry after {delay:.2f}s (exponential backoff, attempt {attempt + 1}/{self.max_retries})")

                # Wait before retry
                await asyncio.sleep(delay)

        # Classify and raise error
        classified_error = self._classify_error(
            last_exception,
            context=operation_name,
            operation=operation_name
        )
        raise classified_error

    async def get_flight_status(self, flight_number: str, flight_date: str) -> Dict[str, Any]:
        """
        Get flight status for a specific flight and date.

        Endpoint: GET /flights/number/{flight_number}/{date}
        Tier: TIER 2 (2 credits per call)

        Args:
            flight_number: Flight number (e.g., "BA123")
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            Flight status data dictionary

        Raises:
            AeroDataBoxError: On API failure
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        # Validate date format
        try:
            datetime.strptime(flight_date, "%Y-%m-%d")
        except ValueError:
            raise AeroDataBoxClientError(
                message=f"Invalid date format: {flight_date}. Expected YYYY-MM-DD",
                status_code=400,
                context="get_flight_status"
            )

        async def _get_flight():
            url = f"{self.base_url}/flights/number/{flight_number}/{flight_date}"
            logger.info(f"Fetching flight status: {flight_number} on {flight_date}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.json()

        return await self._retry_with_backoff(_get_flight)

    async def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """
        Get airport information by IATA code.

        Endpoint: GET /airports/iata/{code}
        Tier: TIER 1 (1 credit per call)

        Args:
            airport_code: IATA airport code (e.g., "JFK")

        Returns:
            Airport information dictionary

        Raises:
            AeroDataBoxError: On API failure
        """
        # Normalize airport code (uppercase, 3 chars)
        airport_code = airport_code.upper()[:3]

        if len(airport_code) != 3:
            raise AeroDataBoxClientError(
                message=f"Invalid airport code: {airport_code}. Must be 3 characters",
                status_code=400,
                context="get_airport_info"
            )

        async def _get_airport():
            url = f"{self.base_url}/airports/iata/{airport_code}"
            logger.info(f"Fetching airport info: {airport_code}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.json()

        return await self._retry_with_backoff(_get_airport)

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.

        Args:
            lat1: Latitude of first point (degrees)
            lon1: Longitude of first point (degrees)
            lat2: Latitude of second point (degrees)
            lon2: Longitude of second point (degrees)

        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0

        # Convert degrees to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return round(distance, 2)

    async def calculate_flight_distance(self, departure_airport: str, arrival_airport: str) -> float:
        """
        Calculate distance between two airports using their coordinates.

        Args:
            departure_airport: Departure airport IATA code
            arrival_airport: Arrival airport IATA code

        Returns:
            Distance in kilometers

        Raises:
            AeroDataBoxError: If airport info cannot be retrieved
        """
        # Get airport info for both airports
        departure_info = await self.get_airport_info(departure_airport)
        arrival_info = await self.get_airport_info(arrival_airport)

        # Extract coordinates
        dep_lat = departure_info.get("location", {}).get("lat")
        dep_lon = departure_info.get("location", {}).get("lon")
        arr_lat = arrival_info.get("location", {}).get("lat")
        arr_lon = arrival_info.get("location", {}).get("lon")

        # Validate coordinates
        if None in (dep_lat, dep_lon, arr_lat, arr_lon):
            raise AeroDataBoxClientError(
                message="Missing coordinates in airport data",
                status_code=400,
                context="calculate_flight_distance",
                details={
                    "departure_airport": departure_airport,
                    "arrival_airport": arrival_airport,
                    "departure_coords": {"lat": dep_lat, "lon": dep_lon},
                    "arrival_coords": {"lat": arr_lat, "lon": arr_lon}
                }
            )

        # Calculate distance
        distance = self.calculate_distance(dep_lat, dep_lon, arr_lat, arr_lon)

        logger.info(f"Calculated distance {departure_airport}-{arrival_airport}: {distance} km")
        return distance

    async def get_airport_departures(
        self,
        origin_icao: str,
        from_local: str,
        to_local: str
    ) -> Dict[str, Any]:
        """
        Get all departures from an airport using FIDS (Flight Information Display System) endpoint.

        This endpoint returns all flights departing from an airport within a specified time window.
        The withLeg=true parameter ensures destination information is included.

        Endpoint: GET /flights/airports/icao/{icao}/{fromLocal}/{toLocal}?withLeg=true&direction=Departure
        Tier: TIER 2 (2 credits per call)

        Args:
            origin_icao: Origin airport ICAO code (e.g., "EDDM" for Munich)
            from_local: Start of time window in ISO format (e.g., "2025-01-15T00:00")
            to_local: End of time window in ISO format (e.g., "2025-01-15T23:59")

        Returns:
            API response containing list of departing flights with leg information

        Raises:
            AeroDataBoxError: On API failure

        Example:
            >>> service = AeroDataBoxService()
            >>> result = await service.get_airport_departures("EDDM", "2025-01-15T00:00", "2025-01-15T23:59")
        """
        # Normalize ICAO code
        origin_icao = origin_icao.upper()

        if len(origin_icao) != 4:
            raise AeroDataBoxClientError(
                message=f"Invalid ICAO code: {origin_icao}. Must be 4 characters",
                status_code=400,
                context="get_airport_departures"
            )

        async def _get_departures():
            url = f"{self.base_url}/flights/airports/icao/{origin_icao}/{from_local}/{to_local}"
            params = {
                "withLeg": "true",
                "direction": "Departure"
            }

            logger.info(f"Fetching departures from {origin_icao} ({from_local} to {to_local})")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                return response.json()

        return await self._retry_with_backoff(_get_departures)

    async def find_flights_by_route(
        self,
        origin_icao: str,
        destination_icao: str,
        departure_date: str,
        airline_iata: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Find flights by route using FIDS endpoint with local filtering.

        Since AeroDataBox doesn't have a direct origin-to-destination search,
        this method:
        1. Fetches all departures from the origin airport for a 24-hour window
        2. Filters locally by destination ICAO
        3. Optionally filters by airline IATA code
        4. Returns matching flights with full details

        Args:
            origin_icao: Origin airport ICAO code (e.g., "EDDM" for Munich)
            destination_icao: Destination airport ICAO code (e.g., "KJFK" for JFK)
            departure_date: Departure date in ISO format (YYYY-MM-DD)
            airline_iata: Optional airline IATA code for filtering (e.g., "LH", "DL")

        Returns:
            List of matching flight dictionaries with standardized fields:
            - flightNumber: Flight number
            - airline: Airline name
            - airlineIata: Airline IATA code
            - departureAirport: Origin airport ICAO
            - arrivalAirport: Destination airport ICAO
            - scheduledDeparture: Scheduled departure time (ISO 8601)
            - scheduledArrival: Scheduled arrival time (ISO 8601)
            - actualDeparture: Actual departure time if available
            - actualArrival: Actual arrival time if available
            - status: Flight status
            - delayMinutes: Delay in minutes if applicable

        Raises:
            AeroDataBoxError: On API failure

        Example:
            >>> service = AeroDataBoxService()
            >>> flights = await service.find_flights_by_route("EDDM", "KJFK", "2025-01-15", "LH")
            >>> for flight in flights:
            ...     print(f"{flight['flightNumber']}: {flight['scheduledDeparture']}")
        """
        # Validate date format
        try:
            parsed_date = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            raise AeroDataBoxClientError(
                message=f"Invalid date format: {departure_date}. Expected YYYY-MM-DD",
                status_code=400,
                context="find_flights_by_route"
            )

        # Normalize inputs
        origin_icao = origin_icao.upper()
        destination_icao = destination_icao.upper()
        if airline_iata:
            airline_iata = airline_iata.upper()

        logger.info(
            f"Searching route {origin_icao} → {destination_icao} on {departure_date}"
            f"{f' (airline: {airline_iata})' if airline_iata else ''}"
        )

        # FIDS endpoint has a 12-hour maximum window restriction
        # We need to make two API calls to cover the full day:
        # 1. Morning/midday: 00:00-11:59
        # 2. Afternoon/evening: 12:00-23:59
        all_flights = []

        # First window: 00:00-11:59
        try:
            from_local_1 = f"{departure_date}T00:00"
            to_local_1 = f"{departure_date}T11:59"
            logger.info(f"Fetching morning flights ({from_local_1} to {to_local_1})")
            response_1 = await self.get_airport_departures(origin_icao, from_local_1, to_local_1)

            # Parse response
            if isinstance(response_1, dict) and "departures" in response_1:
                all_flights.extend(response_1["departures"])
            elif isinstance(response_1, list):
                all_flights.extend(response_1)
        except AeroDataBoxFlightNotFoundError:
            logger.info(f"No morning departures from {origin_icao}")
        except Exception as e:
            logger.warning(f"Error fetching morning flights: {str(e)}")

        # Second window: 12:00-23:59
        try:
            from_local_2 = f"{departure_date}T12:00"
            to_local_2 = f"{departure_date}T23:59"
            logger.info(f"Fetching afternoon/evening flights ({from_local_2} to {to_local_2})")
            response_2 = await self.get_airport_departures(origin_icao, from_local_2, to_local_2)

            # Parse response
            if isinstance(response_2, dict) and "departures" in response_2:
                all_flights.extend(response_2["departures"])
            elif isinstance(response_2, list):
                all_flights.extend(response_2)
        except AeroDataBoxFlightNotFoundError:
            logger.info(f"No afternoon/evening departures from {origin_icao}")
        except Exception as e:
            logger.warning(f"Error fetching afternoon/evening flights: {str(e)}")

        if not all_flights:
            logger.info(f"No departures found from {origin_icao} on {departure_date}")
            return []

        # Filter by destination ICAO and optionally by airline IATA
        matching_flights = []

        for flight_data in all_flights:
            try:
                # Extract arrival airport
                arrival = flight_data.get("arrival", {})
                if not arrival:
                    continue

                arr_airport = arrival.get("airport", {})
                arr_icao = arr_airport.get("icao")

                # Check destination match
                if arr_icao != destination_icao:
                    continue

                # Check airline match if specified
                if airline_iata:
                    airline = flight_data.get("airline", {})
                    flight_airline_iata = airline.get("iata") if airline else None

                    if flight_airline_iata != airline_iata:
                        continue

                # Extract flight information
                flight_number = flight_data.get("number", "")

                # Airline info
                airline = flight_data.get("airline", {})
                airline_name = airline.get("name") if airline else None
                flight_airline_iata = airline.get("iata") if airline else None

                # Departure info
                departure = flight_data.get("departure", {})
                dep_airport = departure.get("airport", {}) if departure else {}
                dep_icao = dep_airport.get("icao") if dep_airport else None

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

                # Build standardized flight object
                standardized_flight = {
                    "flightNumber": flight_number,
                    "airline": airline_name,
                    "airlineIata": flight_airline_iata,
                    "departureAirport": dep_icao or origin_icao,
                    "arrivalAirport": arr_icao,
                    "scheduledDeparture": scheduled_departure,
                    "scheduledArrival": scheduled_arrival,
                    "actualDeparture": actual_departure,
                    "actualArrival": actual_arrival,
                    "status": status,
                    "delayMinutes": delay_minutes,
                }

                matching_flights.append(standardized_flight)

            except Exception as e:
                logger.warning(f"Error parsing flight data: {str(e)}")
                continue

        logger.info(
            f"Found {len(matching_flights)} flights from {origin_icao} to {destination_icao}"
            f"{f' on {airline_iata}' if airline_iata else ''}"
        )

        return matching_flights


# Convenience function with exact signature requested
async def findFlightsByRoute(
    originIcao: str,
    destinationIcao: str,
    departureDate: str,
    airlineIata: str
) -> list[Dict[str, Any]]:
    """
    Find flights by route using the FIDS endpoint (convenience function).

    This is a standalone convenience function that wraps the AeroDataBoxService.find_flights_by_route
    method with the exact signature requested.

    Args:
        originIcao: Origin airport ICAO code (e.g., "EDDM")
        destinationIcao: Destination airport ICAO code (e.g., "KJFK")
        departureDate: Departure date in YYYY-MM-DD format
        airlineIata: Airline IATA code (e.g., "LH", "DL", "UAL")

    Returns:
        List of matching flight objects with:
        - flightNumber: Flight number
        - airline: Airline name
        - airlineIata: Airline IATA code
        - scheduledDeparture: Scheduled departure time (ISO 8601)
        - scheduledArrival: Scheduled arrival time (ISO 8601)
        - status: Flight status
        - delayMinutes: Delay in minutes (if available)

    Example:
        >>> flights = await findFlightsByRoute("EDDM", "KJFK", "2025-01-15", "LH")
        >>> for flight in flights:
        ...     print(f"{flight['flightNumber']}: {flight['scheduledDeparture']}")
    """
    service = aerodatabox_service
    return await service.find_flights_by_route(
        origin_icao=originIcao,
        destination_icao=destinationIcao,
        departure_date=departureDate,
        airline_iata=airlineIata
    )


# Global singleton instance
aerodatabox_service = AeroDataBoxService(
    max_retries=config.AERODATABOX_MAX_RETRIES,
    base_delay=1.0,
    max_delay=60.0
)
