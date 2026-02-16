"""Flight data service - orchestration layer for flight verification.

This service orchestrates:
- CacheService: Check Redis cache first (24h TTL) - FAST
- FlightDataCacheRepository: Check permanent database cache - NEVER PAY TWICE
- QuotaTrackingService: Check quota availability (emergency brake at 95%)
- AeroDataBoxService: Call API only if no cache hit (save money!)
- CompensationService: Calculate EU261 compensation
- FlightDataRepository: Store API snapshot for audit trail
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models import Claim, FlightData
from app.repositories.flight_data_repository import FlightDataRepository
from app.repositories.flight_data_cache_repository import (
    FlightDataCacheRepository,
    FlightNotFoundLogRepository
)
from app.services.cache_service import CacheService
from app.services.aerodatabox_service import aerodatabox_service
from app.services.quota_tracking_service import QuotaTrackingService
from app.services.compensation_service import CompensationService
from app.exceptions import (
    AeroDataBoxError,
    AeroDataBoxQuotaExceededError,
    AeroDataBoxFlightNotFoundError
)

logger = logging.getLogger(__name__)


class FlightDataService:
    """
    Orchestration service for flight verification and enrichment.

    New Flow (Never Pay Twice!):
    1. Check Redis cache (24h TTL) - FAST
    2. Check FlightDataCache (permanent) - FREE
    3. Check FlightNotFoundLog (avoid wasted calls) - FREE
    4. If quota OK, call AeroDataBox API (PAY ONLY IF NEEDED)
    5. Track API usage
    6. Cache result in Redis + FlightDataCache
    7. Calculate compensation
    8. Store FlightData snapshot
    9. Return enriched data
    """

    @classmethod
    async def verify_and_enrich_claim(
        cls,
        session: AsyncSession,
        claim: Claim,
        user_id: Optional[UUID] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Verify flight data and enrich claim with compensation calculation.

        This is the main entry point for flight verification.
        NOW WITH PERMANENT DATABASE CACHING - Never pay twice!

        Args:
            session: Database session
            claim: Claim object to verify and enrich
            user_id: User ID who triggered verification
            force_refresh: Force API call even if cached (admin refresh)

        Returns:
            Enriched claim data dictionary with flight verification results

        Raises:
            AeroDataBoxError: On API failure (gracefully handled by caller)
        """
        logger.info(
            f"Starting flight verification for claim {claim.id}: "
            f"flight {claim.flight_number} on {claim.departure_date}"
        )

        # Check if API is enabled
        if not config.AERODATABOX_ENABLED:
            logger.warning("AeroDataBox API is disabled (AERODATABOX_ENABLED=false)")
            return cls._create_manual_verification_response(claim)

        # Initialize response
        enriched_data = {
            "verified": False,
            "verification_source": "failed",
            "flight_number": claim.flight_number,
            "flight_date": claim.departure_date,
            "airline_name": claim.airline,
            "departure_airport": claim.departure_airport,
            "arrival_airport": claim.arrival_airport,
            "distance_km": None,
            "delay_minutes": None,
            "delay_hours": None,
            "flight_status": None,
            "compensation_amount": None,
            "compensation_tier": None,
            "eligible": None,
            "api_credits_used": 0,
            "cached": False
        }

        flight_data_dict = None
        api_credits_used = 0

        try:
            # Step 1: Check Redis cache (unless force_refresh)
            if not force_refresh:
                cached_flight = await CacheService.get_cached_flight(
                    claim.flight_number,
                    claim.departure_date.strftime("%Y-%m-%d")
                )

                if cached_flight:
                    logger.info(f"Using Redis cached flight data for {claim.flight_number}")
                    flight_data_dict = cached_flight.get("data")
                    enriched_data["cached"] = True
                    enriched_data["verification_source"] = "cached"

            # Step 2: Check permanent database cache (NEW! Never pay twice!)
            if flight_data_dict is None and not force_refresh:
                cache_repo = FlightDataCacheRepository(session)
                db_cached = await cache_repo.get_fresh_or_none(
                    claim.flight_number,
                    claim.departure_date
                )

                if db_cached:
                    if db_cached.is_permanently_not_found:
                        # Flight was previously marked as not found by API
                        logger.info(
                            f"Flight {claim.flight_number} on {claim.departure_date} "
                            f"was previously marked as permanently not found. Skipping API call."
                        )
                        enriched_data["verification_source"] = "not_found_permanent"
                        return enriched_data

                    # Use cached data!
                    logger.info(
                        f"Using database cached flight data for {claim.flight_number} "
                        f"(saved {db_cached.cache_hits} API calls so far!)"
                    )
                    flight_data_dict = db_cached.to_api_response()
                    enriched_data["cached"] = True
                    enriched_data["verification_source"] = "historical_db"

                    # Also cache in Redis for next time
                    await CacheService.cache_flight(
                        claim.flight_number,
                        claim.departure_date.strftime("%Y-%m-%d"),
                        flight_data_dict,
                        ttl=config.FLIGHT_CACHE_TTL_SECONDS
                    )

            # Step 3: Check FlightNotFoundLog (avoid wasted API calls)
            if flight_data_dict is None and not force_refresh:
                not_found_repo = FlightNotFoundLogRepository(session)
                not_found_entry = await not_found_repo.get_by_flight_and_date(
                    claim.flight_number,
                    claim.departure_date
                )

                if not_found_entry:
                    logger.info(
                        f"Flight {claim.flight_number} on {claim.departure_date} "
                        f"previously returned 404 from API (checked {not_found_entry.check_count} times). "
                        f"Skipping API call to save credits."
                    )
                    enriched_data["verification_source"] = "not_found_logged"
                    return enriched_data

            # Step 4: If no cache, call API
            if flight_data_dict is None:
                # Check quota availability (emergency brake at 95%)
                quota_available = await QuotaTrackingService.check_quota_available(session)

                if not quota_available:
                    logger.error(
                        f"API quota exceeded (>95%). Cannot verify flight {claim.flight_number}"
                    )
                    raise AeroDataBoxQuotaExceededError(
                        message="API quota exceeded. Manual verification required.",
                        context="verify_and_enrich_claim"
                    )

                # Call AeroDataBox API
                start_time = datetime.now()

                try:
                    # Get flight status (TIER 2 = 2 credits)
                    api_response = await aerodatabox_service.get_flight_status(
                        claim.flight_number,
                        claim.departure_date.strftime("%Y-%m-%d")
                    )

                    # Calculate response time
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                    # Track API call
                    await QuotaTrackingService.track_api_call(
                        session=session,
                        endpoint=f"/flights/number/{claim.flight_number}/{claim.departure_date}",
                        tier_level="TIER_2",
                        credits_used=2,
                        http_status=200,
                        response_time_ms=response_time_ms,
                        triggered_by_user_id=user_id,
                        claim_id=claim.id
                    )

                    api_credits_used = 2
                    flight_data_dict = api_response
                    enriched_data["verification_source"] = "aerodatabox"

                    # Cache the result in Redis (24h)
                    await CacheService.cache_flight(
                        claim.flight_number,
                        claim.departure_date.strftime("%Y-%m-%d"),
                        flight_data_dict,
                        ttl=config.FLIGHT_CACHE_TTL_SECONDS
                    )

                    # Also cache in permanent database (NEW!)
                    await cls._cache_flight_data_permanently(
                        session,
                        claim.flight_number,
                        claim.departure_date,
                        flight_data_dict
                    )

                    logger.info(f"Successfully retrieved flight data from AeroDataBox API")

                except AeroDataBoxFlightNotFoundError as e:
                    # Flight not found - log it to avoid future API calls
                    logger.warning(f"Flight not found in AeroDataBox: {claim.flight_number}")

                    not_found_repo = FlightNotFoundLogRepository(session)
                    await not_found_repo.log_not_found(
                        flight_number=claim.flight_number,
                        flight_date=claim.departure_date,
                        departure_airport=claim.departure_airport,
                        arrival_airport=claim.arrival_airport,
                        error_code="404",
                        error_message=str(e),
                        claim_id=claim.id
                    )

                    # Also mark in FlightDataCache
                    cache_repo = FlightDataCacheRepository(session)
                    await cache_repo.mark_as_not_found(
                        claim.flight_number,
                        claim.departure_date
                    )

                    enriched_data["verification_source"] = "not_found"
                    return enriched_data

                except AeroDataBoxError as e:
                    # Track failed API call
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                    await QuotaTrackingService.track_api_call(
                        session=session,
                        endpoint=f"/flights/number/{claim.flight_number}/{claim.departure_date}",
                        tier_level="TIER_2",
                        credits_used=0,  # No credits charged on error
                        http_status=getattr(e, 'status_code', None),
                        response_time_ms=response_time_ms,
                        error_message=str(e),
                        triggered_by_user_id=user_id,
                        claim_id=claim.id
                    )

                    logger.error(f"AeroDataBox API error: {str(e)}")
                    raise  # Re-raise for caller to handle

            # Step 5: Parse flight data
            parsed_data = cls._parse_flight_data(flight_data_dict, claim)

            # Step 6: Calculate distance (if not in parsed data)
            if parsed_data.get("distance_km") is None:
                try:
                    distance = await cls._calculate_distance(
                        claim.departure_airport,
                        claim.arrival_airport
                    )
                    parsed_data["distance_km"] = distance

                    # Track airport info calls if made (2x TIER 1 = 2 credits)
                    if not enriched_data["cached"]:
                        api_credits_used += 2

                except Exception as e:
                    logger.warning(f"Failed to calculate distance: {str(e)}")
                    # Use CompensationService fallback
                    distance = await CompensationService.calculate_distance(
                        claim.departure_airport,
                        claim.arrival_airport,
                        use_api=True  # Will try API then hardcoded
                    )
                    parsed_data["distance_km"] = distance if distance else None

            # Step 7: Calculate compensation
            compensation_result = await cls._calculate_compensation(claim, parsed_data)

            # Step 8: Store FlightData snapshot
            flight_data_record = await cls._store_flight_data(
                session,
                claim,
                parsed_data,
                flight_data_dict
            )

            # Step 9: Build enriched response
            enriched_data.update({
                "verified": True,
                "distance_km": float(parsed_data.get("distance_km")) if parsed_data.get("distance_km") else None,
                "delay_minutes": parsed_data.get("delay_minutes"),
                "delay_hours": round(parsed_data.get("delay_minutes") / 60, 2) if parsed_data.get("delay_minutes") else None,
                "flight_status": parsed_data.get("flight_status"),
                "airline_name": parsed_data.get("airline_name") or claim.airline,
                "compensation_amount": compensation_result.get("amount"),
                "compensation_tier": compensation_result.get("tier"),
                "eligible": compensation_result.get("eligible"),
                "api_credits_used": api_credits_used
            })

            logger.info(
                f"Flight verification complete for claim {claim.id}: "
                f"verified={enriched_data['verified']}, "
                f"compensation={enriched_data['compensation_amount']} EUR, "
                f"cached={enriched_data['cached']}, "
                f"source={enriched_data['verification_source']}"
            )

            return enriched_data

        except AeroDataBoxQuotaExceededError:
            # Quota exceeded - return manual verification response
            logger.warning(f"Quota exceeded, falling back to manual verification for claim {claim.id}")
            return cls._create_manual_verification_response(claim)

        except AeroDataBoxFlightNotFoundError:
            # Flight not found - return not verified response
            logger.warning(f"Flight not found in AeroDataBox: {claim.flight_number}")
            enriched_data["verification_source"] = "not_found"
            return enriched_data

        except Exception as e:
            # Unexpected error - log and return manual verification
            logger.error(
                f"Unexpected error during flight verification for claim {claim.id}: {str(e)}",
                exc_info=True
            )
            return cls._create_manual_verification_response(claim)

    @classmethod
    async def _cache_flight_data_permanently(
        cls,
        session: AsyncSession,
        flight_number: str,
        flight_date: datetime.date,
        api_response: Dict[str, Any]
    ) -> None:
        """
        Store flight data in permanent cache for future reuse.

        This is the key to "never pay twice" - we store the API response
        permanently so future claims for the same flight don't need API calls.

        Args:
            session: Database session
            flight_number: Flight number
            flight_date: Flight date
            api_response: Full API response to cache
        """
        try:
            # Parse the API response
            flight_data = cls._extract_flight_data_from_response(api_response)

            # Add airport codes from the response if available
            if isinstance(api_response, list) and len(api_response) > 0:
                flight = api_response[0]
            elif isinstance(api_response, dict):
                flight = api_response
            else:
                flight = {}

            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})
            airline = flight.get("airline", {})

            # Extract IATA codes
            departure_iata = departure.get("airport", {}).get("iata") if departure else None
            arrival_iata = arrival.get("airport", {}).get("iata") if arrival else None
            airline_iata = airline.get("iata") if airline else None

            # Parse scheduled times
            scheduled_departure = None
            scheduled_arrival = None
            actual_departure = None
            actual_arrival = None

            if flight_data.get("scheduled_departure"):
                try:
                    scheduled_departure = datetime.fromisoformat(
                        flight_data["scheduled_departure"].replace('Z', '+00:00')
                    )
                except:
                    pass

            if flight_data.get("scheduled_arrival"):
                try:
                    scheduled_arrival = datetime.fromisoformat(
                        flight_data["scheduled_arrival"].replace('Z', '+00:00')
                    )
                except:
                    pass

            if flight_data.get("actual_departure"):
                try:
                    actual_departure = datetime.fromisoformat(
                        flight_data["actual_departure"].replace('Z', '+00:00')
                    )
                except:
                    pass

            if flight_data.get("actual_arrival"):
                try:
                    actual_arrival = datetime.fromisoformat(
                        flight_data["actual_arrival"].replace('Z', '+00:00')
                    )
                except:
                    pass

            # Calculate distance if in response
            distance_km = None
            if flight.get("distance") and flight["distance"].get("km"):
                distance_km = Decimal(str(flight["distance"]["km"]))

            # Create cache data dict
            cache_data = {
                "airline_iata": airline_iata,
                "airline_name": flight_data.get("airline_name"),
                "departure_airport_iata": departure_iata or "",
                "arrival_airport_iata": arrival_iata or "",
                "scheduled_departure": scheduled_departure,
                "scheduled_arrival": scheduled_arrival,
                "actual_departure": actual_departure,
                "actual_arrival": actual_arrival,
                "flight_status": flight_data.get("flight_status"),
                "delay_minutes": flight_data.get("delay_minutes"),
                "distance_km": distance_km
            }

            # Store in permanent cache
            cache_repo = FlightDataCacheRepository(session)
            await cache_repo.create_or_update(
                flight_number=flight_number,
                flight_date=flight_date,
                flight_data=cache_data,
                api_response_raw=api_response
            )

            logger.info(
                f"Permanently cached flight data for {flight_number} on {flight_date} "
                f"(will reuse for future claims without API cost)"
            )

        except Exception as e:
            # Don't fail the whole operation if caching fails
            logger.warning(f"Failed to cache flight data permanently: {str(e)}")

    @classmethod
    def _extract_flight_data_from_response(cls, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract flight data from API response for permanent caching."""
        # Handle both single flight and list response
        if isinstance(api_response, list) and len(api_response) > 0:
            flight = api_response[0]
        elif isinstance(api_response, dict):
            flight = api_response
        else:
            return {}

        # Extract airline info
        airline = flight.get("airline", {})
        airline_name = airline.get("name") if airline else None

        # Extract departure info
        departure = flight.get("departure", {})
        scheduled_departure = departure.get("scheduledTime", {}).get("utc") if departure else None
        actual_departure = departure.get("actualTime", {}).get("utc") if departure else None

        # Extract arrival info
        arrival = flight.get("arrival", {})
        scheduled_arrival = arrival.get("scheduledTime", {}).get("utc") if arrival else None
        actual_arrival = arrival.get("actualTime", {}).get("utc") if arrival else None

        # Calculate delay
        delay_minutes = None
        if scheduled_arrival and actual_arrival:
            try:
                scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
                actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
                delay_minutes = int((actual - scheduled).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"Failed to calculate delay: {str(e)}")

        # Flight status
        status = flight.get("status", "scheduled")

        return {
            "airline_name": airline_name,
            "flight_status": status,
            "scheduled_departure": scheduled_departure,
            "actual_departure": actual_departure,
            "scheduled_arrival": scheduled_arrival,
            "actual_arrival": actual_arrival,
            "delay_minutes": delay_minutes
        }

    @classmethod
    def _parse_flight_data(cls, api_response: Dict[str, Any], claim: Claim) -> Dict[str, Any]:
        """
        Parse AeroDataBox API response into structured data.

        Args:
            api_response: Raw API response
            claim: Claim object

        Returns:
            Parsed flight data dictionary
        """
        # Handle both single flight and list response
        if isinstance(api_response, list) and len(api_response) > 0:
            flight = api_response[0]
        elif isinstance(api_response, dict):
            flight = api_response
        else:
            raise ValueError(f"Unexpected API response format: {type(api_response)}")

        # Extract airline info
        airline = flight.get("airline", {})
        airline_name = airline.get("name") if airline else None

        # Extract departure info
        departure = flight.get("departure", {})
        scheduled_departure = departure.get("scheduledTime", {}).get("utc") if departure else None
        actual_departure = departure.get("actualTime", {}).get("utc") if departure else None

        # Extract arrival info
        arrival = flight.get("arrival", {})
        scheduled_arrival = arrival.get("scheduledTime", {}).get("utc") if arrival else None
        actual_arrival = arrival.get("actualTime", {}).get("utc") if arrival else None

        # Calculate delay
        delay_minutes = None
        if scheduled_arrival and actual_arrival:
            try:
                scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
                actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
                delay_minutes = int((actual - scheduled).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"Failed to calculate delay: {str(e)}")

        # Flight status
        status = flight.get("status", "scheduled")

        return {
            "airline_name": airline_name,
            "flight_status": status,
            "scheduled_departure": scheduled_departure,
            "actual_departure": actual_departure,
            "scheduled_arrival": scheduled_arrival,
            "actual_arrival": actual_arrival,
            "delay_minutes": delay_minutes,
            "distance_km": None,  # Calculated separately if needed
            "raw_response": flight
        }

    @classmethod
    async def _calculate_distance(cls, departure_iata: str, arrival_iata: str) -> Optional[float]:
        """
        Calculate distance between airports using AeroDataBox API.

        Args:
            departure_iata: Departure airport IATA
            arrival_iata: Arrival airport IATA

        Returns:
            Distance in kilometers or None
        """
        try:
            distance = await aerodatabox_service.calculate_flight_distance(
                departure_iata,
                arrival_iata
            )
            return distance
        except Exception as e:
            logger.error(f"Failed to calculate distance via API: {str(e)}")
            return None

    @classmethod
    async def _calculate_compensation(cls, claim: Claim, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate EU261 compensation using CompensationService.

        Args:
            claim: Claim object
            flight_data: Parsed flight data

        Returns:
            Compensation calculation result
        """
        try:
            # Get distance
            distance_km = flight_data.get("distance_km")
            if not distance_km:
                return {"amount": None, "tier": None, "eligible": None}

            # Get delay hours
            delay_minutes = flight_data.get("delay_minutes")
            delay_hours = delay_minutes / 60 if delay_minutes else None

            # Use CompensationService
            compensation = await CompensationService.calculate_compensation(
                departure_airport=claim.departure_airport,
                arrival_airport=claim.arrival_airport,
                distance_km=float(distance_km),
                delay_hours=delay_hours,
                incident_type=claim.incident_type,
                use_api=False  # Distance already provided, no need for API call
            )

            # Determine tier
            tier = CompensationService._get_distance_tier(float(distance_km))

            return {
                "amount": compensation["amount"],
                "tier": tier,
                "eligible": compensation["eligible"]
            }

        except Exception as e:
            logger.error(f"Failed to calculate compensation: {str(e)}")
            return {"amount": None, "tier": None, "eligible": None}

    @classmethod
    async def _store_flight_data(
        cls,
        session: AsyncSession,
        claim: Claim,
        parsed_data: Dict[str, Any],
        raw_response: Dict[str, Any]
    ) -> FlightData:
        """
        Store FlightData snapshot in database for audit trail.

        Args:
            session: Database session
            claim: Claim object
            parsed_data: Parsed flight data
            raw_response: Raw API response

        Returns:
            Created FlightData record
        """
        repo = FlightDataRepository(session)

        # Create FlightData record
        flight_data = FlightData(
            claim_id=claim.id,
            flight_number=claim.flight_number,
            flight_date=claim.departure_date,
            airline_name=parsed_data.get("airline_name"),
            departure_airport_iata=claim.departure_airport,
            arrival_airport_iata=claim.arrival_airport,
            distance_km=Decimal(str(parsed_data["distance_km"])) if parsed_data.get("distance_km") else None,
            scheduled_departure=datetime.fromisoformat(parsed_data["scheduled_departure"].replace('Z', '+00:00')) if parsed_data.get("scheduled_departure") else None,
            scheduled_arrival=datetime.fromisoformat(parsed_data["scheduled_arrival"].replace('Z', '+00:00')) if parsed_data.get("scheduled_arrival") else None,
            actual_departure=datetime.fromisoformat(parsed_data["actual_departure"].replace('Z', '+00:00')) if parsed_data.get("actual_departure") else None,
            actual_arrival=datetime.fromisoformat(parsed_data["actual_arrival"].replace('Z', '+00:00')) if parsed_data.get("actual_arrival") else None,
            flight_status=parsed_data.get("flight_status"),
            delay_minutes=parsed_data.get("delay_minutes"),
            api_source="aerodatabox",
            api_response_raw=raw_response
        )

        session.add(flight_data)
        await session.flush()

        logger.info(f"Stored FlightData snapshot for claim {claim.id}")

        return flight_data

    @classmethod
    def _create_manual_verification_response(cls, claim: Claim) -> Dict[str, Any]:
        """
        Create response for manual verification (fallback when API unavailable).

        Args:
            claim: Claim object

        Returns:
            Manual verification response dictionary
        """
        return {
            "verified": False,
            "verification_source": "manual",
            "flight_number": claim.flight_number,
            "flight_date": claim.departure_date,
            "airline_name": claim.airline,
            "departure_airport": claim.departure_airport,
            "arrival_airport": claim.arrival_airport,
            "distance_km": None,
            "delay_minutes": None,
            "delay_hours": None,
            "flight_status": None,
            "compensation_amount": None,
            "compensation_tier": None,
            "eligible": None,
            "api_credits_used": 0,
            "cached": False
        }

    @classmethod
    async def get_cache_stats(cls, session: AsyncSession) -> Dict[str, Any]:
        """
        Get statistics about the flight data cache.

        Returns:
            Dictionary with cache statistics showing API savings
        """
        cache_repo = FlightDataCacheRepository(session)
        return await cache_repo.get_cache_stats()
