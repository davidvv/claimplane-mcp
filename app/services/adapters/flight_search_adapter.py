"""Flight search provider adapter interface.

This module defines the abstract interface for flight search providers,
allowing the application to switch between different APIs (AeroDataBox,
AviationStack, etc.) without changing the service layer code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class FlightSearchAdapter(ABC):
    """Abstract base class for flight search providers.

    Implementations must provide:
    - Route search (all flights from A to B on a specific date)
    - Airport search (autocomplete for airport IATA codes)
    """

    @abstractmethod
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
            List of flight dictionaries in standardized format:
            [
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
                    "actualDeparture": "2025-01-15T16:45:00+01:00",  # or None
                    "actualArrival": "2025-01-15T20:20:00-05:00",    # or None
                    "status": "delayed",  # or "scheduled", "cancelled", etc.
                    "delayMinutes": 180,  # or None
                    "distanceKm": 6200.0,  # or None
                },
                ...
            ]

        Raises:
            AeroDataBoxError: If API call fails
        """
        pass

    @abstractmethod
    async def search_airports(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search airports by IATA code, name, or city.

        Args:
            query: Search query (e.g., "munich", "MUC", "New York")
            limit: Maximum number of results to return

        Returns:
            List of airport dictionaries in standardized format:
            [
                {
                    "iata": "MUC",
                    "icao": "EDDM",
                    "name": "Munich Airport",
                    "city": "Munich",
                    "country": "Germany"
                },
                ...
            ]

        Raises:
            AeroDataBoxError: If API call fails
        """
        pass
