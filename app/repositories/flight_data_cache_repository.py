"""Repository for FlightDataCache model - permanent flight data storage."""
from typing import Optional, Dict, Any
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FlightDataCache, AirportCache, FlightNotFoundLog
from app.repositories.base import BaseRepository


class FlightDataCacheRepository(BaseRepository[FlightDataCache]):
    """Repository for FlightDataCache - permanent reusable flight data storage."""

    def __init__(self, session: AsyncSession):
        super().__init__(FlightDataCache, session)

    async def get_by_flight_and_date(
        self,
        flight_number: str,
        flight_date: date
    ) -> Optional[FlightDataCache]:
        """
        Get cached flight data by flight number and date.

        Args:
            flight_number: Flight number (e.g., "UA988")
            flight_date: Flight date

        Returns:
            FlightDataCache or None if not found
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        result = await self.session.execute(
            select(FlightDataCache)
            .where(
                and_(
                    FlightDataCache.flight_number == flight_number,
                    FlightDataCache.flight_date == flight_date
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_fresh_or_none(
        self,
        flight_number: str,
        flight_date: date,
        force_refresh: bool = False
    ) -> Optional[FlightDataCache]:
        """
        Get cached flight data only if it's fresh (not stale).

        Args:
            flight_number: Flight number
            flight_date: Flight date
            force_refresh: If True, always return None (will trigger API call)

        Returns:
            FlightDataCache if found and fresh, None otherwise
        """
        if force_refresh:
            return None

        cached = await self.get_by_flight_and_date(flight_number, flight_date)

        if not cached:
            return None

        # Check if permanently not found
        if cached.is_permanently_not_found:
            return cached  # Return it so caller knows it was marked as not found

        # Check if stale
        if cached.is_stale:
            return None  # Will trigger refresh via API

        # Data is fresh - increment hit counter
        await self._increment_cache_hits(cached.id)

        return cached

    async def _increment_cache_hits(self, cache_id: UUID) -> None:
        """Increment the cache_hits counter for a cached flight."""
        await self.session.execute(
            update(FlightDataCache)
            .where(FlightDataCache.id == cache_id)
            .values(
                cache_hits=FlightDataCache.cache_hits + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )

    async def create_or_update(
        self,
        flight_number: str,
        flight_date: date,
        flight_data: Dict[str, Any],
        api_response_raw: Optional[Dict[str, Any]] = None
    ) -> FlightDataCache:
        """
        Create or update cached flight data.

        Args:
            flight_number: Flight number
            flight_date: Flight date
            flight_data: Parsed flight data dictionary
            api_response_raw: Full raw API response (optional)

        Returns:
            Created or updated FlightDataCache
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        # Try to get existing
        existing = await self.get_by_flight_and_date(flight_number, flight_date)

        if existing:
            # Update existing
            existing.airline_iata = flight_data.get("airline_iata")
            existing.airline_name = flight_data.get("airline_name")
            existing.departure_airport_iata = flight_data.get("departure_airport_iata")
            existing.arrival_airport_iata = flight_data.get("arrival_airport_iata")
            existing.scheduled_departure = flight_data.get("scheduled_departure")
            existing.scheduled_arrival = flight_data.get("scheduled_arrival")
            existing.actual_departure = flight_data.get("actual_departure")
            existing.actual_arrival = flight_data.get("actual_arrival")
            existing.flight_status = flight_data.get("flight_status")
            existing.delay_minutes = flight_data.get("delay_minutes")
            existing.distance_km = flight_data.get("distance_km")
            existing.api_response_raw = api_response_raw
            existing.last_refreshed_at = datetime.now(timezone.utc)
            existing.is_permanently_not_found = False
            existing.updated_at = datetime.now(timezone.utc)

            await self.session.flush()
            return existing
        else:
            # Create new
            cache_entry = FlightDataCache(
                flight_number=flight_number,
                flight_date=flight_date,
                airline_iata=flight_data.get("airline_iata"),
                airline_name=flight_data.get("airline_name"),
                departure_airport_iata=flight_data.get("departure_airport_iata"),
                arrival_airport_iata=flight_data.get("arrival_airport_iata"),
                scheduled_departure=flight_data.get("scheduled_departure"),
                scheduled_arrival=flight_data.get("scheduled_arrival"),
                actual_departure=flight_data.get("actual_departure"),
                actual_arrival=flight_data.get("actual_arrival"),
                flight_status=flight_data.get("flight_status"),
                delay_minutes=flight_data.get("delay_minutes"),
                distance_km=flight_data.get("distance_km"),
                api_response_raw=api_response_raw,
                last_refreshed_at=datetime.now(timezone.utc),
                is_permanently_not_found=False,
                cache_hits=0
            )

            self.session.add(cache_entry)
            await self.session.flush()
            return cache_entry

    async def mark_as_not_found(
        self,
        flight_number: str,
        flight_date: date
    ) -> FlightDataCache:
        """
        Mark a flight as permanently not found (API returned 404).

        This prevents future API calls for flights that don't exist
        or are too old for the API to return.

        Args:
            flight_number: Flight number
            flight_date: Flight date

        Returns:
            Updated FlightDataCache entry
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        existing = await self.get_by_flight_and_date(flight_number, flight_date)

        if existing:
            existing.is_permanently_not_found = True
            existing.not_found_checked_at = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing
        else:
            # Create entry marked as not found
            cache_entry = FlightDataCache(
                flight_number=flight_number,
                flight_date=flight_date,
                departure_airport_iata="",  # Required field
                arrival_airport_iata="",   # Required field
                is_permanently_not_found=True,
                not_found_checked_at=datetime.now(timezone.utc),
                cache_hits=0
            )
            self.session.add(cache_entry)
            await self.session.flush()
            return cache_entry

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the flight data cache.

        Returns:
            Dictionary with cache statistics
        """
        from sqlalchemy import func

        # Total entries
        total_result = await self.session.execute(
            select(func.count(FlightDataCache.id))
        )
        total_entries = total_result.scalar_one()

        # Not found entries
        not_found_result = await self.session.execute(
            select(func.count(FlightDataCache.id))
            .where(FlightDataCache.is_permanently_not_found == True)
        )
        not_found_entries = not_found_result.scalar_one()

        # Total cache hits
        hits_result = await self.session.execute(
            select(func.sum(FlightDataCache.cache_hits))
        )
        total_hits = hits_result.scalar_one() or 0

        # Stale entries
        stale_result = await self.session.execute(
            select(func.count(FlightDataCache.id))
            .where(
                and_(
                    FlightDataCache.is_permanently_not_found == False,
                    FlightDataCache.last_refreshed_at < datetime.now(timezone.utc) - FlightDataCache.configurable_stale_days * 86400  # seconds in a day
                )
            )
        )
        stale_entries = stale_result.scalar_one()

        return {
            "total_entries": total_entries,
            "not_found_entries": not_found_entries,
            "valid_entries": total_entries - not_found_entries,
            "total_cache_hits": total_hits,
            "stale_entries": stale_entries,
            "api_calls_saved": total_hits  # Each hit = one saved API call
        }


class AirportCacheRepository(BaseRepository[AirportCache]):
    """Repository for AirportCache - permanent airport information storage."""

    def __init__(self, session: AsyncSession):
        super().__init__(AirportCache, session)

    async def get_by_iata(self, iata_code: str) -> Optional[AirportCache]:
        """
        Get cached airport by IATA code.

        Args:
            iata_code: 3-letter IATA code (e.g., "FRA")

        Returns:
            AirportCache or None if not found
        """
        iata_code = iata_code.upper()

        result = await self.session.execute(
            select(AirportCache)
            .where(AirportCache.iata_code == iata_code)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        iata_code: str,
        airport_data: Dict[str, Any],
        api_response_raw: Optional[Dict[str, Any]] = None
    ) -> AirportCache:
        """
        Create or update cached airport data.

        Args:
            iata_code: 3-letter IATA code
            airport_data: Parsed airport data dictionary
            api_response_raw: Full raw API response (optional)

        Returns:
            Created or updated AirportCache
        """
        iata_code = iata_code.upper()

        existing = await self.get_by_iata(iata_code)

        if existing:
            # Update existing
            existing.icao_code = airport_data.get("icao_code")
            existing.name = airport_data.get("name")
            existing.city = airport_data.get("city")
            existing.country_code = airport_data.get("country_code")
            existing.country_name = airport_data.get("country_name")
            existing.latitude = airport_data.get("latitude")
            existing.longitude = airport_data.get("longitude")
            existing.timezone = airport_data.get("timezone")
            existing.api_response_raw = api_response_raw
            existing.updated_at = datetime.now(timezone.utc)

            await self.session.flush()
            return existing
        else:
            # Create new
            cache_entry = AirportCache(
                iata_code=iata_code,
                icao_code=airport_data.get("icao_code"),
                name=airport_data.get("name"),
                city=airport_data.get("city"),
                country_code=airport_data.get("country_code"),
                country_name=airport_data.get("country_name"),
                latitude=airport_data.get("latitude"),
                longitude=airport_data.get("longitude"),
                timezone=airport_data.get("timezone"),
                api_response_raw=api_response_raw,
                cache_hits=0
            )

            self.session.add(cache_entry)
            await self.session.flush()
            return cache_entry

    async def _increment_cache_hits(self, cache_id: UUID) -> None:
        """Increment the cache_hits counter for a cached airport."""
        await self.session.execute(
            update(AirportCache)
            .where(AirportCache.id == cache_id)
            .values(
                cache_hits=AirportCache.cache_hits + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )


class FlightNotFoundLogRepository(BaseRepository[FlightNotFoundLog]):
    """Repository for FlightNotFoundLog - track flights that API cannot find."""

    def __init__(self, session: AsyncSession):
        super().__init__(FlightNotFoundLog, session)

    async def get_by_flight_and_date(
        self,
        flight_number: str,
        flight_date: date
    ) -> Optional[FlightNotFoundLog]:
        """
        Check if a flight has been marked as not found before.

        Args:
            flight_number: Flight number
            flight_date: Flight date

        Returns:
            FlightNotFoundLog or None if flight was never marked not found
        """
        flight_number = flight_number.upper().replace(" ", "")

        result = await self.session.execute(
            select(FlightNotFoundLog)
            .where(
                and_(
                    FlightNotFoundLog.flight_number == flight_number,
                    FlightNotFoundLog.flight_date == flight_date,
                    FlightNotFoundLog.was_found_later == False  # Still marked as not found
                )
            )
        )
        return result.scalar_one_or_none()

    async def log_not_found(
        self,
        flight_number: str,
        flight_date: date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        claim_id: Optional[UUID] = None
    ) -> FlightNotFoundLog:
        """
        Log that a flight was not found by the API.

        Args:
            flight_number: Flight number
            flight_date: Flight date
            departure_airport: Departure airport IATA (optional)
            arrival_airport: Arrival airport IATA (optional)
            error_code: API error code (e.g., "404")
            error_message: Error message from API
            claim_id: ID of claim that triggered this check

        Returns:
            Created or updated FlightNotFoundLog entry
        """
        flight_number = flight_number.upper().replace(" ", "")

        existing = await self.get_by_flight_and_date(flight_number, flight_date)

        if existing:
            # Update existing - increment check count
            existing.check_count = existing.check_count + 1
            existing.last_checked_at = datetime.now(timezone.utc)
            existing.last_claim_id = claim_id
            existing.api_error_code = error_code or existing.api_error_code
            existing.api_error_message = error_message or existing.api_error_message

            await self.session.flush()
            return existing
        else:
            # Create new entry
            log_entry = FlightNotFoundLog(
                flight_number=flight_number,
                flight_date=flight_date,
                departure_airport=departure_airport.upper() if departure_airport else None,
                arrival_airport=arrival_airport.upper() if arrival_airport else None,
                api_error_code=error_code,
                api_error_message=error_message,
                last_claim_id=claim_id,
                check_count=1
            )

            self.session.add(log_entry)
            await self.session.flush()
            return log_entry

    async def mark_as_found(
        self,
        flight_number: str,
        flight_date: date
    ) -> Optional[FlightNotFoundLog]:
        """
        Mark a previously not-found flight as now found.

        This is rare but can happen if the API updates its data.

        Args:
            flight_number: Flight number
            flight_date: Flight date

        Returns:
            Updated FlightNotFoundLog or None if not found
        """
        flight_number = flight_number.upper().replace(" ", "")

        existing = await self.get_by_flight_and_date(flight_number, flight_date)

        if existing:
            existing.was_found_later = True
            existing.found_later_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        return None
