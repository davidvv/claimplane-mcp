"""Flight search service for route-based flight discovery.

This service orchestrates the flight search flow with:
- 8-step orchestration (cache → quota → API → parse → filter → sort)
- Provider adapter pattern for API flexibility
- Comprehensive caching and error handling
- Analytics tracking for business intelligence
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.services.cache_service import CacheService
from app.services.quota_tracking_service import QuotaTrackingService
from app.services.adapters.flight_search_adapter import FlightSearchAdapter
from app.services.adapters.aerodatabox_route_adapter import AeroDataBoxRouteAdapter
from app.services.compensation_service import CompensationService
from app.models import FlightSearchLog
from app.exceptions import (
    AeroDataBoxError,
    AeroDataBoxQuotaExceededError,
    AeroDataBoxFlightNotFoundError
)

logger = logging.getLogger(__name__)


class FlightSearchService:
    """
    Service for searching flights by route and time.

    8-step orchestration flow:
    1. Validate inputs (IATA codes, date range)
    2. Check cache (24h TTL)
    3. Check quota availability (emergency brake at 95%)
    4. Call provider adapter (AeroDataBoxRouteAdapter or alternative)
    5. Track API usage
    6. Cache result
    7. Parse and filter results (by time if specified)
    8. Sort (delayed/cancelled first, then by departure time) and return
    """

    @classmethod
    def _get_provider_adapter(cls) -> FlightSearchAdapter:
        """
        Get configured flight search provider adapter.

        Returns:
            FlightSearchAdapter instance based on config

        Raises:
            ValueError: If unknown provider specified
        """
        provider = config.FLIGHT_SEARCH_PROVIDER

        if provider == "aerodatabox":
            return AeroDataBoxRouteAdapter()
        # Future providers can be added here
        # elif provider == "aviationstack":
        #     return AviationStackAdapter()
        else:
            logger.warning(f"Unknown flight search provider '{provider}', defaulting to AeroDataBox")
            return AeroDataBoxRouteAdapter()

    @classmethod
    async def search_flights_by_route(
        cls,
        session: AsyncSession,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str,
        approximate_time: Optional[str] = None,
        user_id: Optional[UUID] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Search for flights on a specific route and date.

        8-step orchestration flow with caching, quota tracking, and analytics.

        Args:
            session: Database session
            departure_iata: Departure airport IATA code (e.g., "MUC")
            arrival_iata: Arrival airport IATA code (e.g., "JFK")
            flight_date: Flight date in YYYY-MM-DD format
            approximate_time: Optional time filter ("morning"|"afternoon"|"evening"|"HH:MM")
            user_id: User who triggered search (for analytics)
            force_refresh: Bypass cache

        Returns:
            {
                "flights": [...],  # List of FlightSearchResult dicts
                "total": 12,
                "cached": false,
                "apiCreditsUsed": 2
            }

        Raises:
            AeroDataBoxError: If API call fails (gracefully returns empty list)
        """
        # Step 1: Normalize inputs
        departure_iata = departure_iata.upper()
        arrival_iata = arrival_iata.upper()

        logger.info(
            f"Route search: {departure_iata} → {arrival_iata} on {flight_date} "
            f"(time: {approximate_time or 'any'}, user: {user_id})"
        )

        # Step 2: Check cache (unless force_refresh)
        cached_result = None
        if not force_refresh:
            cached_result = await CacheService.get_cached_route_search(
                departure_iata,
                arrival_iata,
                flight_date
            )

            if cached_result:
                flights = cached_result.get("data", [])

                # Client-side time filtering (cache omits time for better hit rate)
                if approximate_time:
                    flights = cls._filter_by_time(flights, approximate_time)

                # Sort results
                flights = cls._sort_flights(flights)

                logger.info(
                    f"Cache HIT: {len(flights)} flights for {departure_iata} → {arrival_iata}"
                )

                # Track analytics (cached search)
                if config.FLIGHT_SEARCH_ANALYTICS_ENABLED:
                    await cls._track_search_analytics(
                        session=session,
                        departure_iata=departure_iata,
                        arrival_iata=arrival_iata,
                        flight_date=flight_date,
                        approximate_time=approximate_time,
                        results_count=len(flights),
                        user_id=user_id
                    )

                return {
                    "flights": flights,
                    "total": len(flights),
                    "cached": True,
                    "apiCreditsUsed": 0
                }

        # Step 3: Check quota availability
        quota_available = await QuotaTrackingService.check_quota_available(session)
        if not quota_available:
            logger.error("API quota exceeded (>95%), cannot perform route search")

            # Track analytics (quota exceeded)
            if config.FLIGHT_SEARCH_ANALYTICS_ENABLED:
                await cls._track_search_analytics(
                    session=session,
                    departure_iata=departure_iata,
                    arrival_iata=arrival_iata,
                    flight_date=flight_date,
                    approximate_time=approximate_time,
                    results_count=0,
                    user_id=user_id
                )

            # Graceful degradation: return empty result
            return {
                "flights": [],
                "total": 0,
                "cached": False,
                "apiCreditsUsed": 0,
                "error": "API quota exceeded. Please try again later."
            }

        # Step 4: Call provider adapter
        provider = cls._get_provider_adapter()
        start_time = datetime.now()

        try:
            # Make API call
            flights = await provider.search_route(
                departure_iata=departure_iata,
                arrival_iata=arrival_iata,
                flight_date=flight_date
            )

            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                f"API call successful: {len(flights)} flights found in {response_time_ms}ms"
            )

            # Step 5: Track API usage
            await QuotaTrackingService.track_api_call(
                session=session,
                endpoint=f"/flights/{departure_iata}/{arrival_iata}/{flight_date}",
                tier_level="TIER_2",  # AeroDataBox route search is TIER_2
                credits_used=2,
                http_status=200,
                response_time_ms=response_time_ms,
                triggered_by_user_id=user_id,
                claim_id=None  # No claim yet (pre-submission search)
            )

            # Step 6: Cache result (omit time for maximum cache hits)
            await CacheService.cache_route_search(
                departure_iata=departure_iata,
                arrival_iata=arrival_iata,
                flight_date=flight_date,
                flights=flights
            )

            # Step 7: Parse and filter results
            if approximate_time:
                flights = cls._filter_by_time(flights, approximate_time)

            # Add estimated compensation for each flight
            flights = cls._add_estimated_compensation(flights)

            # Step 8: Sort results
            flights = cls._sort_flights(flights)

            # Track analytics
            if config.FLIGHT_SEARCH_ANALYTICS_ENABLED:
                await cls._track_search_analytics(
                    session=session,
                    departure_iata=departure_iata,
                    arrival_iata=arrival_iata,
                    flight_date=flight_date,
                    approximate_time=approximate_time,
                    results_count=len(flights),
                    user_id=user_id
                )

            return {
                "flights": flights,
                "total": len(flights),
                "cached": False,
                "apiCreditsUsed": 2
            }

        except AeroDataBoxFlightNotFoundError:
            # No flights found - not an error, just empty result
            logger.info(f"No flights found on route {departure_iata} → {arrival_iata}")

            # Track analytics (no results)
            if config.FLIGHT_SEARCH_ANALYTICS_ENABLED:
                await cls._track_search_analytics(
                    session=session,
                    departure_iata=departure_iata,
                    arrival_iata=arrival_iata,
                    flight_date=flight_date,
                    approximate_time=approximate_time,
                    results_count=0,
                    user_id=user_id
                )

            return {
                "flights": [],
                "total": 0,
                "cached": False,
                "apiCreditsUsed": 2
            }

        except AeroDataBoxError as e:
            # API error - graceful degradation
            logger.error(f"Route search API error: {str(e)}")

            # Track analytics (error)
            if config.FLIGHT_SEARCH_ANALYTICS_ENABLED:
                await cls._track_search_analytics(
                    session=session,
                    departure_iata=departure_iata,
                    arrival_iata=arrival_iata,
                    flight_date=flight_date,
                    approximate_time=approximate_time,
                    results_count=0,
                    user_id=user_id
                )

            return {
                "flights": [],
                "total": 0,
                "cached": False,
                "apiCreditsUsed": 0,
                "error": "Flight search temporarily unavailable. Please try entering your flight number manually."
            }

    @classmethod
    async def search_airports(
        cls,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search airports by IATA code, name, or city.

        Uses provider adapter with 7-day caching.

        Args:
            query: Search query (e.g., "munich", "MUC")
            limit: Maximum number of results to return

        Returns:
            List of airport dictionaries
        """
        query_normalized = query.strip().upper()

        logger.info(f"Airport search: '{query}' (limit: {limit})")

        # Check cache first
        cached_results = await CacheService.get_cached_airport_search(query_normalized)
        if cached_results:
            airports = cached_results.get("data", [])[:limit]
            logger.info(f"Cache HIT: {len(airports)} airports for query '{query}'")
            return airports

        # Call provider adapter
        provider = cls._get_provider_adapter()

        try:
            airports = await provider.search_airports(query_normalized, limit)

            # Cache results (7-day TTL)
            await CacheService.cache_airport_search(query_normalized, airports)

            logger.info(f"Airport search: {len(airports)} results for '{query}'")
            return airports

        except AeroDataBoxError as e:
            logger.error(f"Airport search error: {str(e)}")
            return []

    @classmethod
    def _filter_by_time(
        cls,
        flights: List[Dict[str, Any]],
        approximate_time: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter flights by approximate time.

        Time filters:
        - "morning": 06:00-12:00
        - "afternoon": 12:00-18:00
        - "evening": 18:00-23:59
        - "HH:MM": ±3 hours from specified time

        Args:
            flights: List of flight dictionaries
            approximate_time: Time filter

        Returns:
            Filtered list of flights
        """
        if not approximate_time:
            return flights

        approximate_time = approximate_time.lower().strip()

        # Time range definitions
        time_ranges = {
            "morning": (time(6, 0), time(12, 0)),
            "afternoon": (time(12, 0), time(18, 0)),
            "evening": (time(18, 0), time(23, 59))
        }

        filtered_flights = []

        for flight in flights:
            scheduled_departure = flight.get("scheduledDeparture")
            if not scheduled_departure:
                continue

            try:
                # Parse departure time
                dep_dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                dep_time = dep_dt.time()

                # Check if matches filter
                if approximate_time in time_ranges:
                    # Predefined time range
                    start_time, end_time = time_ranges[approximate_time]
                    if start_time <= dep_time <= end_time:
                        filtered_flights.append(flight)

                elif ':' in approximate_time:
                    # HH:MM format: ±3 hours window
                    try:
                        target_hour, target_minute = map(int, approximate_time.split(':'))
                        target_time = time(target_hour, target_minute)

                        # Convert to minutes for comparison
                        dep_minutes = dep_time.hour * 60 + dep_time.minute
                        target_minutes = target_time.hour * 60 + target_time.minute

                        # ±3 hours = 180 minutes
                        if abs(dep_minutes - target_minutes) <= 180:
                            filtered_flights.append(flight)
                    except ValueError:
                        # Invalid time format, skip filter
                        filtered_flights.append(flight)

            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing departure time: {str(e)}")
                continue

        logger.info(
            f"Time filter '{approximate_time}': {len(filtered_flights)}/{len(flights)} flights"
        )

        return filtered_flights

    @classmethod
    def _sort_flights(cls, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort flights by eligibility and departure time.

        Sort order:
        1. Delayed/cancelled flights first (more likely eligible for compensation)
        2. Then by departure time (ascending)

        Args:
            flights: List of flight dictionaries

        Returns:
            Sorted list of flights
        """
        def sort_key(flight):
            # Primary sort: Delayed/cancelled flights first
            delay_minutes = flight.get("delayMinutes", 0) or 0
            status = flight.get("status", "").lower()

            is_eligible = (delay_minutes >= 180) or (status == "cancelled")
            priority = 0 if is_eligible else 1

            # Secondary sort: Departure time
            scheduled_departure = flight.get("scheduledDeparture", "")
            try:
                dep_dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                dep_timestamp = dep_dt.timestamp()
            except (ValueError, AttributeError):
                dep_timestamp = float('inf')

            return (priority, dep_timestamp)

        sorted_flights = sorted(flights, key=sort_key)

        return sorted_flights

    @classmethod
    def _add_estimated_compensation(cls, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add estimated EU261 compensation to each flight.

        Args:
            flights: List of flight dictionaries

        Returns:
            Flights with estimatedCompensation field added
        """
        for flight in flights:
            try:
                distance_km = flight.get("distanceKm")
                delay_minutes = flight.get("delayMinutes")
                status = flight.get("status", "").lower()

                if not distance_km:
                    flight["estimatedCompensation"] = None
                    continue

                # Calculate compensation based on distance and delay
                if status == "cancelled":
                    # Cancelled flights: compensation based on distance only
                    if distance_km < 1500:
                        compensation = 250
                    elif distance_km < 3500:
                        compensation = 400
                    else:
                        compensation = 600
                elif delay_minutes and delay_minutes >= 180:
                    # Delayed flights: must be ≥ 3 hours
                    if distance_km < 1500:
                        compensation = 250
                    elif distance_km < 3500:
                        compensation = 400
                    else:
                        compensation = 600
                else:
                    compensation = None

                flight["estimatedCompensation"] = compensation

            except Exception as e:
                logger.warning(f"Error calculating compensation: {str(e)}")
                flight["estimatedCompensation"] = None

        return flights

    @classmethod
    async def _track_search_analytics(
        cls,
        session: AsyncSession,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str,
        approximate_time: Optional[str],
        results_count: int,
        user_id: Optional[UUID]
    ) -> None:
        """
        Track route search for analytics and business intelligence.

        Args:
            session: Database session
            departure_iata: Departure airport IATA
            arrival_iata: Arrival airport IATA
            flight_date: Flight date
            approximate_time: Time filter (if any)
            results_count: Number of results found
            user_id: User who performed search
        """
        try:
            search_log = FlightSearchLog(
                departure_airport=departure_iata,
                arrival_airport=arrival_iata,
                search_date=datetime.strptime(flight_date, "%Y-%m-%d").date(),
                search_time=approximate_time,
                results_count=results_count,
                user_id=user_id
            )

            session.add(search_log)
            await session.commit()

            logger.debug(
                f"Tracked search analytics: {departure_iata} → {arrival_iata}, "
                f"{results_count} results"
            )

        except Exception as e:
            logger.error(f"Error tracking search analytics: {str(e)}")
            # Don't fail the search if analytics tracking fails
            await session.rollback()
