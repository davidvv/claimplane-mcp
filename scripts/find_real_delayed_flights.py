#!/usr/bin/env python3
"""
Script to find real flights with delays and cancellations from past 2 weeks.

This script uses the AeroDataBox API to search for:
- 3 flights with delays < 3 hours
- 3 flights with delays > 3 hours
- 3 cancelled flights

The results can be used for testing the claim submission flow.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
from app.config import config
from app.exceptions import AeroDataBoxError


# Major European flights that operate daily and are likely to have delays
MAJOR_FLIGHTS = [
    # British Airways
    ("BA", "303"),   # London-Paris
    ("BA", "304"),   # Paris-London
    ("BA", "903"),   # London-Frankfurt
    ("BA", "904"),   # Frankfurt-London
    ("BA", "475"),   # London-Barcelona
    ("BA", "476"),   # Barcelona-London

    # Lufthansa
    ("LH", "400"),   # Frankfurt-Munich
    ("LH", "401"),   # Munich-Frankfurt
    ("LH", "110"),   # Frankfurt-London
    ("LH", "111"),   # London-Frankfurt
    ("LH", "2222"),  # Munich-Berlin

    # Air France
    ("AF", "1216"),  # Paris-London
    ("AF", "1217"),  # London-Paris
    ("AF", "1518"),  # Paris-Amsterdam
    ("AF", "1519"),  # Amsterdam-Paris

    # KLM
    ("KL", "1000"),  # Amsterdam-London
    ("KL", "1001"),  # London-Amsterdam
    ("KL", "1234"),  # Amsterdam-Paris

    # Ryanair (low-cost, higher delay probability)
    ("FR", "166"),   # Dublin-London
    ("FR", "8"),     # Various routes
    ("FR", "1432"),

    # EasyJet
    ("U2", "8321"),  # London-Amsterdam
    ("U2", "2085"),  # Various routes
]


class FlightFinder:
    """Find real flights with delays and cancellations."""

    def __init__(self):
        self.flights_under_3h = []
        self.flights_over_3h = []
        self.flights_cancelled = []
        self.api_calls = 0
        self.successful_calls = 0
        self.errors = []
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        if "api.market" in config.AERODATABOX_BASE_URL.lower():
            return {
                "x-api-market-key": config.AERODATABOX_API_KEY,
                "accept": "application/json",
                "User-Agent": f"ClaimPlane/{config.API_VERSION}"
            }
        elif "rapidapi.com" in config.AERODATABOX_BASE_URL.lower():
            return {
                "X-RapidAPI-Key": config.AERODATABOX_API_KEY,
                "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
                "Accept": "application/json"
            }
        else:
            return {
                "X-API-Key": config.AERODATABOX_API_KEY,
                "Accept": "application/json"
            }

    async def search_flights(self, days_back: int = 14):
        """
        Search for delayed and cancelled flights over the past N days.

        Args:
            days_back: Number of days to search back (default: 14 = 2 weeks)
        """
        print(f"\n{'='*80}")
        print(f"SEARCHING FOR REAL DELAYED/CANCELLED FLIGHTS")
        print(f"{'='*80}\n")
        print(f"API Base URL: {config.AERODATABOX_BASE_URL}")
        print(f"Search period: {days_back} days back")
        print(f"Target: 3 flights each category (under 3h, over 3h, cancelled)\n")

        if not config.AERODATABOX_API_KEY:
            print("❌ ERROR: AERODATABOX_API_KEY not configured in .env file")
            return

        # Search recent dates (starting from 2 days ago to allow for complete data)
        today = date.today()
        start_date = today - timedelta(days=2)

        for days_ago in range(2, min(days_back + 2, 16)):  # Cap at 16 days
            flight_date = today - timedelta(days=days_ago)
            flight_date_str = flight_date.strftime("%Y-%m-%d")

            # Skip if we already have enough flights
            if (len(self.flights_under_3h) >= 3 and
                len(self.flights_over_3h) >= 3 and
                len(self.flights_cancelled) >= 3):
                print(f"\n✅ Found enough flights! Stopping search.")
                break

            print(f"\n📅 Date: {flight_date_str} ({days_ago} days ago)")

            # Try different flight numbers on this date
            for airline_code, flight_num in MAJOR_FLIGHTS:
                flight_number = f"{airline_code}{flight_num}"

                try:
                    # Check this specific flight
                    found = await self._check_flight(flight_number, flight_date_str)

                    # Stop if we have enough
                    if (len(self.flights_under_3h) >= 3 and
                        len(self.flights_over_3h) >= 3 and
                        len(self.flights_cancelled) >= 3):
                        break

                    # Small delay to avoid rate limiting (only if we got results)
                    if found:
                        await asyncio.sleep(0.3)

                except Exception as e:
                    # Continue with next flight
                    continue

            # Status update
            print(f"   Progress: Under 3h: {len(self.flights_under_3h)}/3 | "
                  f"Over 3h: {len(self.flights_over_3h)}/3 | "
                  f"Cancelled: {len(self.flights_cancelled)}/3 | "
                  f"API calls: {self.successful_calls}/{self.api_calls}")

    async def _check_flight(self, flight_number: str, flight_date: str) -> bool:
        """
        Check a specific flight for delays/cancellations.

        Returns:
            True if flight data was found and processed, False otherwise
        """
        self.api_calls += 1

        try:
            url = f"{config.AERODATABOX_BASE_URL}/flights/number/{flight_number}/{flight_date}"

            async with httpx.AsyncClient(timeout=config.AERODATABOX_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)

                # Handle non-200 responses
                if response.status_code == 404:
                    return False  # Flight doesn't exist

                if response.status_code != 200:
                    return False

                # Parse JSON
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return False

                if not data:
                    return False

                self.successful_calls += 1

                # Parse response (can be list or single object)
                flights = data if isinstance(data, list) else [data]

                for flight in flights:
                    # Extract flight info
                    flight_info = self._parse_flight_info(flight, flight_number, flight_date)

                    if not flight_info:
                        continue

                    # Categorize by delay/cancellation
                    if flight_info["is_cancelled"]:
                        if len(self.flights_cancelled) < 3:
                            self.flights_cancelled.append(flight_info)
                            print(f"   ❌ CANCELLED: {flight_info['display_name']}")
                            return True

                    elif flight_info["delay_minutes"]:
                        delay_hours = flight_info["delay_minutes"] / 60

                        if delay_hours < 3 and len(self.flights_under_3h) < 3:
                            self.flights_under_3h.append(flight_info)
                            print(f"   🟡 DELAY <3h: {flight_info['display_name']} "
                                  f"({flight_info['delay_minutes']} min)")
                            return True

                        elif delay_hours >= 3 and len(self.flights_over_3h) < 3:
                            self.flights_over_3h.append(flight_info)
                            print(f"   🔴 DELAY >3h: {flight_info['display_name']} "
                                  f"({flight_info['delay_minutes']} min)")
                            return True

                return False

        except httpx.TimeoutException:
            return False
        except Exception as e:
            return False

    def _parse_flight_info(self, flight: Dict[str, Any], flight_number: str,
                           flight_date: str) -> Dict[str, Any]:
        """
        Parse flight data from API response.

        Returns:
            Parsed flight info dictionary or None if invalid
        """
        try:
            # Extract basic info
            status = flight.get("status", "").lower()

            # Extract departure/arrival airports
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})

            dep_airport = departure.get("airport", {}).get("iata", "")
            arr_airport = arrival.get("airport", {}).get("iata", "")

            # Extract airline
            airline = flight.get("airline", {})
            airline_name = airline.get("name", "")

            # Extract times
            scheduled_arrival_time = arrival.get("scheduledTime", {})
            actual_arrival_time = arrival.get("actualTime", {})

            scheduled_arrival = scheduled_arrival_time.get("utc") if scheduled_arrival_time else None
            actual_arrival = actual_arrival_time.get("utc") if actual_arrival_time else None

            # Calculate delay
            delay_minutes = None
            if scheduled_arrival and actual_arrival:
                try:
                    # Parse UTC times
                    scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
                    actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
                    delay_minutes = int((actual - scheduled).total_seconds() / 60)

                    # Only consider positive delays (early arrivals don't count)
                    if delay_minutes < 0:
                        delay_minutes = None
                except Exception:
                    delay_minutes = None

            # Check if cancelled
            is_cancelled = status in ["cancelled", "canceled"]

            # Skip if no useful data
            if not is_cancelled and not delay_minutes:
                return None

            # Skip if delay is too small (< 30 min doesn't qualify for compensation)
            if delay_minutes and delay_minutes < 30:
                return None

            # Build flight info
            return {
                "flight_number": flight_number,
                "flight_date": flight_date,
                "airline": airline_name,
                "departure_airport": dep_airport,
                "arrival_airport": arr_airport,
                "status": status,
                "is_cancelled": is_cancelled,
                "delay_minutes": delay_minutes,
                "scheduled_arrival": scheduled_arrival,
                "actual_arrival": actual_arrival,
                "display_name": f"{flight_number} {dep_airport}→{arr_airport} on {flight_date}"
            }

        except Exception as e:
            return None

    def print_results(self):
        """Print final results summary."""
        print(f"\n\n{'='*80}")
        print(f"SEARCH RESULTS")
        print(f"{'='*80}\n")
        print(f"Total API calls: {self.api_calls}")
        print(f"Successful calls: {self.successful_calls}")
        print(f"Success rate: {(self.successful_calls/self.api_calls*100) if self.api_calls > 0 else 0:.1f}%\n")

        # Print cancelled flights
        print(f"🔴 CANCELLED FLIGHTS ({len(self.flights_cancelled)}/3):")
        print(f"{'-'*80}")
        if self.flights_cancelled:
            for flight in self.flights_cancelled:
                print(f"  Flight: {flight['flight_number']}")
                print(f"  Route:  {flight['departure_airport']} → {flight['arrival_airport']}")
                print(f"  Date:   {flight['flight_date']}")
                print(f"  Airline: {flight['airline']}")
                print(f"  Status: {flight['status'].upper()}")
                print()
        else:
            print("  No cancelled flights found in the search period\n")

        # Print delays > 3h
        print(f"\n🟠 DELAYS > 3 HOURS ({len(self.flights_over_3h)}/3):")
        print(f"{'-'*80}")
        if self.flights_over_3h:
            for flight in self.flights_over_3h:
                delay_hours = flight['delay_minutes'] / 60
                print(f"  Flight: {flight['flight_number']}")
                print(f"  Route:  {flight['departure_airport']} → {flight['arrival_airport']}")
                print(f"  Date:   {flight['flight_date']}")
                print(f"  Airline: {flight['airline']}")
                print(f"  Delay:  {flight['delay_minutes']} minutes ({delay_hours:.1f} hours)")
                print()
        else:
            print("  No delays >3h found in the search period\n")

        # Print delays < 3h
        print(f"\n🟡 DELAYS < 3 HOURS ({len(self.flights_under_3h)}/3):")
        print(f"{'-'*80}")
        if self.flights_under_3h:
            for flight in self.flights_under_3h:
                delay_hours = flight['delay_minutes'] / 60
                print(f"  Flight: {flight['flight_number']}")
                print(f"  Route:  {flight['departure_airport']} → {flight['arrival_airport']}")
                print(f"  Date:   {flight['flight_date']}")
                print(f"  Airline: {flight['airline']}")
                print(f"  Delay:  {flight['delay_minutes']} minutes ({delay_hours:.1f} hours)")
                print()
        else:
            print("  No delays <3h found in the search period\n")

        # Export to JSON for easy testing
        all_flights = {
            "cancelled": self.flights_cancelled,
            "delays_over_3h": self.flights_over_3h,
            "delays_under_3h": self.flights_under_3h,
            "metadata": {
                "total_flights_found": (
                    len(self.flights_cancelled) +
                    len(self.flights_over_3h) +
                    len(self.flights_under_3h)
                ),
                "api_calls": self.api_calls,
                "successful_calls": self.successful_calls,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

        output_file = "real_delayed_flights.json"
        with open(output_file, "w") as f:
            json.dump(all_flights, f, indent=2)

        print(f"\n✅ Results exported to: {output_file}")

        # Print sample test data if we found anything
        if self.flights_over_3h or self.flights_under_3h or self.flights_cancelled:
            print(f"\n{'='*80}")
            print(f"SAMPLE TEST DATA")
            print(f"{'='*80}")
            print(f"\nYou can use these flights to test your claim submission flow!")

            if self.flights_over_3h:
                sample = self.flights_over_3h[0]
                print(f"\nSample >3h delay (eligible for compensation):")
                print(f"  Flight: {sample['flight_number']}")
                print(f"  Date: {sample['flight_date']}")
                print(f"  Route: {sample['departure_airport']} → {sample['arrival_airport']}")
                print(f"  Delay: {sample['delay_minutes']} minutes")


async def main():
    """Main entry point."""
    finder = FlightFinder()

    try:
        # Search for flights (14 days back)
        await finder.search_flights(days_back=14)

        # Print results
        finder.print_results()

    except KeyboardInterrupt:
        print("\n\n⚠️  Search interrupted by user")
        finder.print_results()
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        finder.print_results()


if __name__ == "__main__":
    asyncio.run(main())
