"""Example usage of findFlightsByRoute function.

This script demonstrates how to use the FIDS-based flight search
to find flights by route using ICAO codes and airline filtering.

Usage:
    python scripts/example_find_flights_by_route.py
    OR
    docker exec flight_claim_api python scripts/example_find_flights_by_route.py
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.aerodatabox_service import findFlightsByRoute
from app.config import config


async def main():
    """Demonstrate findFlightsByRoute function."""

    print("=" * 80)
    print("findFlightsByRoute Example")
    print("=" * 80)

    # Check configuration
    if not config.AERODATABOX_API_KEY:
        print("❌ ERROR: AERODATABOX_API_KEY not configured")
        print("Please set the AERODATABOX_API_KEY environment variable")
        return

    if not config.AERODATABOX_ENABLED:
        print("⚠️  WARNING: AERODATABOX_ENABLED=false")
        print("Set AERODATABOX_ENABLED=true to enable API calls")

    # Example 1: Munich to JFK on Lufthansa
    print("\n" + "=" * 80)
    print("Example 1: Finding Lufthansa flights from Munich (EDDM) to JFK (KJFK)")
    print("=" * 80)

    try:
        flights = await findFlightsByRoute(
            originIcao="EDDM",        # Munich Airport
            destinationIcao="KJFK",   # JFK Airport
            departureDate="2025-01-15",
            airlineIata="LH"          # Lufthansa
        )

        print(f"\n✅ Found {len(flights)} Lufthansa flight(s)")

        for i, flight in enumerate(flights, 1):
            print(f"\nFlight {i}:")
            print(f"  Flight Number: {flight['flightNumber']}")
            print(f"  Airline: {flight['airline']} ({flight['airlineIata']})")
            print(f"  Route: {flight['departureAirport']} → {flight['arrivalAirport']}")
            print(f"  Scheduled Departure: {flight['scheduledDeparture']}")
            print(f"  Scheduled Arrival: {flight['scheduledArrival']}")
            print(f"  Status: {flight['status']}")
            if flight.get('delayMinutes'):
                print(f"  Delay: {flight['delayMinutes']} minutes")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: Today's date with different airline
    print("\n" + "=" * 80)
    print("Example 2: Finding United flights from Frankfurt (EDDF) to Newark (KEWR)")
    print("=" * 80)

    today = datetime.now().date().isoformat()

    try:
        flights = await findFlightsByRoute(
            originIcao="EDDF",        # Frankfurt Airport
            destinationIcao="KEWR",   # Newark Airport
            departureDate=today,
            airlineIata="UA"          # United Airlines
        )

        print(f"\n✅ Found {len(flights)} United flight(s) today")

        for i, flight in enumerate(flights, 1):
            print(f"\nFlight {i}:")
            print(f"  Flight Number: {flight['flightNumber']}")
            print(f"  Airline: {flight['airline']} ({flight['airlineIata']})")
            print(f"  Scheduled Departure: {flight['scheduledDeparture']}")
            print(f"  Status: {flight['status']}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 3: Using the service method directly (for optional airline parameter)
    print("\n" + "=" * 80)
    print("Example 3: Finding ALL flights from Munich to JFK (any airline)")
    print("=" * 80)

    try:
        from app.services.aerodatabox_service import aerodatabox_service

        flights = await aerodatabox_service.find_flights_by_route(
            origin_icao="EDDM",
            destination_icao="KJFK",
            departure_date="2025-01-15",
            airline_iata=None  # No airline filter - get all airlines
        )

        print(f"\n✅ Found {len(flights)} flight(s) from all airlines")

        # Group by airline
        airlines = {}
        for flight in flights:
            airline = flight['airlineIata'] or 'Unknown'
            if airline not in airlines:
                airlines[airline] = []
            airlines[airline].append(flight['flightNumber'])

        print("\nFlights by airline:")
        for airline, flight_numbers in airlines.items():
            print(f"  {airline}: {', '.join(flight_numbers)}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 80)
    print("Examples Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
