"""Test script for AeroDataBox FIDS (Flight Information Display System) endpoint.

This script tests the airport departures endpoint which returns all flights departing
from an airport within a 24-hour window. Used to verify API behavior before implementation.

Endpoint: GET /flights/airports/icao/{icao}/{fromLocal}/{toLocal}?withLeg=true&direction=Departure

Usage:
    python scripts/test_fids_endpoint.py
    OR
    docker exec flight_claim_api python scripts/test_fids_endpoint.py
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.config import config


async def test_fids_endpoint():
    """Test the FIDS endpoint with a known airport."""

    # Test parameters
    origin_icao = "EDDM"  # Munich Airport
    destination_icao = "KJFK"  # JFK Airport
    test_date = datetime.now().date()  # Today

    # Calculate 24-hour window in local time
    # For Munich (UTC+1 in winter, UTC+2 in summer), we'll use UTC for simplicity
    from_local = f"{test_date}T00:00"  # Start of day
    to_local = f"{test_date}T23:59"    # End of day

    # Construct endpoint
    endpoint = f"/flights/airports/icao/{origin_icao}/{from_local}/{to_local}"
    url = f"{config.AERODATABOX_BASE_URL}{endpoint}"

    # Add query parameters
    params = {
        "withLeg": "true",
        "direction": "Departure"
    }

    print("=" * 80)
    print("FIDS Endpoint Test")
    print("=" * 80)
    print(f"Origin ICAO: {origin_icao}")
    print(f"Destination ICAO: {destination_icao} (for filtering)")
    print(f"Date: {test_date}")
    print(f"Time window: {from_local} to {to_local}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("=" * 80)

    # Check if API is configured
    if not config.AERODATABOX_API_KEY:
        print("❌ ERROR: AERODATABOX_API_KEY not configured")
        print("Set the AERODATABOX_API_KEY environment variable")
        return

    if not config.AERODATABOX_ENABLED:
        print("⚠️  WARNING: AERODATABOX_ENABLED=false")
        print("Set AERODATABOX_ENABLED=true to enable API calls")

    # Determine header format based on base URL
    if "rapidapi.com" in config.AERODATABOX_BASE_URL.lower():
        headers = {
            "X-RapidAPI-Key": config.AERODATABOX_API_KEY,
            "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
            "Accept": "application/json"
        }
        print("Using RapidAPI headers")
    elif "api.market" in config.AERODATABOX_BASE_URL.lower():
        headers = {
            "x-api-market-key": config.AERODATABOX_API_KEY,
            "accept": "application/json"
        }
        print("Using API.Market headers")
    else:
        headers = {
            "X-API-Key": config.AERODATABOX_API_KEY,
            "Accept": "application/json"
        }
        print("Using direct AeroDataBox headers")

    print("\n" + "=" * 80)
    print("Making API Request...")
    print("=" * 80)

    # Make request
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)

            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {response.elapsed.total_seconds():.2f}s")

            if response.status_code == 200:
                data = response.json()

                print("\n" + "=" * 80)
                print("✅ SUCCESS - API Response Received")
                print("=" * 80)

                # Analyze response structure
                if isinstance(data, dict):
                    if "departures" in data:
                        flights = data["departures"]
                        print(f"Response type: Dict with 'departures' key")
                    else:
                        flights = [data]
                        print(f"Response type: Single flight dict")
                elif isinstance(data, list):
                    flights = data
                    print(f"Response type: List of flights")
                else:
                    print(f"⚠️  Unexpected response type: {type(data)}")
                    print(f"Response: {data}")
                    return

                print(f"Total departures: {len(flights)}")

                # Filter by destination
                matching_flights = []
                for flight in flights:
                    # Check if flight has leg data (withLeg=true)
                    arrival = flight.get("arrival", {})
                    if arrival:
                        arr_airport = arrival.get("airport", {})
                        arr_icao = arr_airport.get("icao")

                        if arr_icao == destination_icao:
                            matching_flights.append(flight)

                print(f"Flights to {destination_icao}: {len(matching_flights)}")

                # Display first flight as example
                if flights:
                    print("\n" + "=" * 80)
                    print("Example Flight (first in list)")
                    print("=" * 80)
                    example = flights[0]

                    # Extract key fields
                    flight_number = example.get("number", "N/A")
                    airline = example.get("airline", {})
                    airline_name = airline.get("name") if airline else "N/A"
                    airline_iata = airline.get("iata") if airline else "N/A"

                    departure = example.get("departure", {})
                    dep_airport = departure.get("airport", {}) if departure else {}
                    dep_icao = dep_airport.get("icao") if dep_airport else "N/A"
                    dep_iata = dep_airport.get("iata") if dep_airport else "N/A"

                    arrival = example.get("arrival", {})
                    arr_airport = arrival.get("airport", {}) if arrival else {}
                    arr_icao = arr_airport.get("icao") if arr_airport else "N/A"
                    arr_iata = arr_airport.get("iata") if arr_airport else "N/A"

                    scheduled_dep = departure.get("scheduledTime", {}).get("utc") if departure else "N/A"
                    scheduled_arr = arrival.get("scheduledTime", {}).get("utc") if arrival else "N/A"

                    print(f"Flight Number: {flight_number}")
                    print(f"Airline: {airline_name} ({airline_iata})")
                    print(f"Departure: {dep_icao} / {dep_iata}")
                    print(f"Arrival: {arr_icao} / {arr_iata}")
                    print(f"Scheduled Departure: {scheduled_dep}")
                    print(f"Scheduled Arrival: {scheduled_arr}")
                    print(f"Status: {example.get('status', 'N/A')}")

                    print("\nFull flight object keys:")
                    print(", ".join(example.keys()))

                    if arrival:
                        print("\nArrival object keys:")
                        print(", ".join(arrival.keys()))

                # Display matching flight if found
                if matching_flights:
                    print("\n" + "=" * 80)
                    print(f"Example Matching Flight ({origin_icao} → {destination_icao})")
                    print("=" * 80)
                    match = matching_flights[0]

                    flight_number = match.get("number", "N/A")
                    airline = match.get("airline", {})
                    airline_name = airline.get("name") if airline else "N/A"
                    airline_iata = airline.get("iata") if airline else "N/A"

                    print(f"Flight Number: {flight_number}")
                    print(f"Airline: {airline_name} ({airline_iata})")
                    print(f"This flight would match the filter criteria!")
                else:
                    print(f"\n⚠️  No flights found from {origin_icao} to {destination_icao} on {test_date}")
                    print(f"This is normal - not all routes operate daily")

                print("\n" + "=" * 80)
                print("API Structure Analysis")
                print("=" * 80)
                print("✅ withLeg=true parameter works" if matching_flights or len(flights) > 0 else "❌ withLeg=true might not work")
                print("✅ Can filter by destination ICAO" if arrival else "❌ No arrival data available")
                print("✅ Airline IATA available for filtering" if airline_iata != "N/A" else "❌ Airline IATA not available")

            elif response.status_code == 404:
                print("❌ 404 Not Found - Endpoint may not exist or no flights found")
                print(f"Response: {response.text[:500]}")
            elif response.status_code in (401, 403):
                print("❌ Authentication Error - Check API key")
                print(f"Response: {response.text[:500]}")
            elif response.status_code == 429:
                print("❌ Rate Limit Exceeded")
                print(f"Response: {response.text[:500]}")
            else:
                print(f"❌ Error - Status {response.status_code}")
                print(f"Response: {response.text[:500]}")

        except httpx.TimeoutException as e:
            print(f"❌ Timeout Error: {e}")
        except httpx.ConnectError as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("AeroDataBox FIDS Endpoint Test")
    print("Testing airport departures with destination filtering\n")

    asyncio.run(test_fids_endpoint())
