"""Flight data service - orchestration layer for flight verification.

This service orchestrates:
- CacheService: Check cache first (24h TTL)
- QuotaTrackingService: Check quota availability (emergency brake at 95%)
- AeroDataBoxService: Call API if cache miss and quota available
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

    Flow:
    1. Check cache (24h TTL)
    2. If cache miss, check quota availability
    3. If quota OK, call AeroDataBox API
    4. Track API usage
    5. Cache result
    6. Calculate compensation
    7. Store FlightData snapshot
    8. Return enriched data
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
            # Step 1: Check cache (unless force_refresh)
            if not force_refresh:
                cached_flight = await CacheService.get_cached_flight(
                    claim.flight_number,
                    claim.departure_date.strftime("%Y-%m-%d")
                )

                if cached_flight:
                    logger.info(f"Using cached flight data for {claim.flight_number}")
                    flight_data_dict = cached_flight.get("data")
                    enriched_data["cached"] = True
                    enriched_data["verification_source"] = "cached"

            # Step 2: If no cache, call API
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

                    # Cache the result
                    await CacheService.cache_flight(
                        claim.flight_number,
                        claim.departure_date.strftime("%Y-%m-%d"),
                        flight_data_dict,
                        ttl=config.FLIGHT_CACHE_TTL_SECONDS
                    )

                    logger.info(f"Successfully retrieved flight data from AeroDataBox API")

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

            # Step 3: Parse flight data
            parsed_data = cls._parse_flight_data(flight_data_dict, claim)

            # Step 4: Calculate distance (if not in parsed data)
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
                    distance = CompensationService.calculate_distance(
                        claim.departure_airport,
                        claim.arrival_airport
                    )
                    parsed_data["distance_km"] = distance if distance else None

            # Step 5: Calculate compensation
            compensation_result = cls._calculate_compensation(claim, parsed_data)

            # Step 6: Store FlightData snapshot
            flight_data_record = await cls._store_flight_data(
                session,
                claim,
                parsed_data,
                flight_data_dict
            )

            # Step 7: Build enriched response
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
                f"cached={enriched_data['cached']}"
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
    def _calculate_compensation(cls, claim: Claim, flight_data: Dict[str, Any]) -> Dict[str, Any]:
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
            compensation = CompensationService.calculate_compensation(
                distance_km=float(distance_km),
                delay_hours=delay_hours,
                incident_type=claim.incident_type
            )

            # Determine tier
            tier = CompensationService._get_distance_tier(float(distance_km))

            return {
                "amount": Decimal(str(compensation)) if compensation else None,
                "tier": tier,
                "eligible": compensation > 0 if compensation is not None else None
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
