"""Repository for FlightData model CRUD operations."""
from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import FlightData, Claim
from app.repositories.base import BaseRepository


class FlightDataRepository(BaseRepository[FlightData]):
    """Repository for FlightData model with specific query methods."""

    def __init__(self, session: AsyncSession):
        """
        Initialize FlightData repository.

        Args:
            session: Database session
        """
        super().__init__(FlightData, session)

    async def get_by_claim_id(self, claim_id: UUID) -> Optional[FlightData]:
        """
        Get flight data by claim ID.

        Args:
            claim_id: Claim UUID

        Returns:
            FlightData or None if not found
        """
        result = await self.session.execute(
            select(FlightData)
            .where(FlightData.claim_id == claim_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_flight_and_date(
        self,
        flight_number: str,
        flight_date: date
    ) -> Optional[FlightData]:
        """
        Get flight data by flight number and date.

        Args:
            flight_number: Flight number (e.g., "BA123")
            flight_date: Flight date

        Returns:
            FlightData or None if not found
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        result = await self.session.execute(
            select(FlightData)
            .where(
                and_(
                    FlightData.flight_number == flight_number,
                    FlightData.flight_date == flight_date
                )
            )
            .order_by(FlightData.api_retrieved_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_for_flight(
        self,
        flight_number: str,
        flight_date: date
    ) -> List[FlightData]:
        """
        Get all flight data records for a specific flight and date.

        Useful for seeing historical API snapshots.

        Args:
            flight_number: Flight number
            flight_date: Flight date

        Returns:
            List of FlightData records
        """
        # Normalize flight number
        flight_number = flight_number.upper().replace(" ", "")

        result = await self.session.execute(
            select(FlightData)
            .where(
                and_(
                    FlightData.flight_number == flight_number,
                    FlightData.flight_date == flight_date
                )
            )
            .order_by(FlightData.api_retrieved_at.desc())
        )
        return result.scalars().all()

    async def get_with_claim(self, flight_data_id: UUID) -> Optional[FlightData]:
        """
        Get flight data with associated claim loaded.

        Args:
            flight_data_id: FlightData UUID

        Returns:
            FlightData with claim relationship loaded, or None
        """
        result = await self.session.execute(
            select(FlightData)
            .options(selectinload(FlightData.claim))
            .where(FlightData.id == flight_data_id)
        )
        return result.scalar_one_or_none()

    async def get_claims_without_flight_data(self, limit: int = 100) -> List[Claim]:
        """
        Get claims that don't have flight data yet.

        Useful for backfill operations.

        Args:
            limit: Maximum number of claims to return

        Returns:
            List of Claim objects without flight_data
        """
        result = await self.session.execute(
            select(Claim)
            .outerjoin(FlightData, Claim.id == FlightData.claim_id)
            .where(FlightData.id.is_(None))
            .order_by(Claim.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_claims_without_flight_data(self) -> int:
        """
        Count claims without flight data.

        Returns:
            Number of claims without flight_data
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Claim.id))
            .outerjoin(FlightData, Claim.id == FlightData.claim_id)
            .where(FlightData.id.is_(None))
        )
        return result.scalar_one()

    async def get_by_airline(self, airline_iata: str, limit: int = 100) -> List[FlightData]:
        """
        Get flight data by airline IATA code.

        Args:
            airline_iata: Airline IATA code (e.g., "BA")
            limit: Maximum number of records

        Returns:
            List of FlightData records
        """
        airline_iata = airline_iata.upper()

        result = await self.session.execute(
            select(FlightData)
            .where(FlightData.airline_iata == airline_iata)
            .order_by(FlightData.flight_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_route(
        self,
        departure_airport: str,
        arrival_airport: str,
        limit: int = 100
    ) -> List[FlightData]:
        """
        Get flight data by route (departure → arrival).

        Args:
            departure_airport: Departure airport IATA
            arrival_airport: Arrival airport IATA
            limit: Maximum number of records

        Returns:
            List of FlightData records
        """
        departure_airport = departure_airport.upper()
        arrival_airport = arrival_airport.upper()

        result = await self.session.execute(
            select(FlightData)
            .where(
                and_(
                    FlightData.departure_airport_iata == departure_airport,
                    FlightData.arrival_airport_iata == arrival_airport
                )
            )
            .order_by(FlightData.flight_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_delayed_flights(self, min_delay_minutes: int = 180) -> List[FlightData]:
        """
        Get flights with delays >= specified minutes.

        Args:
            min_delay_minutes: Minimum delay in minutes (default: 180 = 3 hours for EU261)

        Returns:
            List of delayed FlightData records
        """
        result = await self.session.execute(
            select(FlightData)
            .where(FlightData.delay_minutes >= min_delay_minutes)
            .order_by(FlightData.delay_minutes.desc())
        )
        return result.scalars().all()

    async def get_cancelled_flights(self) -> List[FlightData]:
        """
        Get cancelled flights.

        Returns:
            List of cancelled FlightData records
        """
        result = await self.session.execute(
            select(FlightData)
            .where(FlightData.flight_status == FlightData.STATUS_CANCELLED)
            .order_by(FlightData.flight_date.desc())
        )
        return result.scalars().all()
