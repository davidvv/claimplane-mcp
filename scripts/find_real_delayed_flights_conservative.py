#!/usr/bin/env python3
"""
CONSERVATIVE VERSION - Limits API calls to save credits.

This script uses the AeroDataBox API to search for real delayed/cancelled flights.
It stops after finding enough flights OR using 50 credits (25 successful API calls).

Target: 3 flights each for testing (under 3h, over 3h, cancelled)
Max API credits: 50 credits (25 calls × 2 credits each)
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
from app.config import config

# Focus on high-traffic routes most likely to have delays
# Limit to just 10 popular flights to reduce API calls
HIGH_TRAFFIC_FLIGHTS = [
    ("BA", "303"),   # London-Paris (very frequent)
    ("BA", "304"),   # Paris-London
    ("LH", "400"),   # Frankfurt-Munich
    ("LH", "110"),   # Frankfurt-London
    ("AF", "1216"),  # Paris-London
    ("KL", "1000"),  # Amsterdam-London
    ("FR", "166"),   # Ryanair Dublin-London (budget = more delays)
    ("U2", "8321"),  # EasyJet (budget = more delays)
    ("BA", "475"),   # London-Barcelona
    ("LH", "111"),   # London-Frankfurt
]

MAX_API_CREDITS = 50  # Stop after using this many credits
MAX_DAYS_SEARCH = 7   # Only search last 7 days (not 14)


class ConservativeFlightFinder:
    """Find flights with minimal API usage."""

    def __init__(self):
        self.flights_under_3h = []
        self.flights_over_3h = []
        self.flights_cancelled = []
        self.api_calls = 0
        self.successful_calls = 0
        self.credits_used = 0
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        if "api.market" in config.AERODATABOX_BASE_URL.lower():
            return {
                "x-api-market-key": config.AERODATABOX_API_KEY,
                "accept": "application/json",
                "User-Agent": f"EasyAirClaim/{config.API_VERSION}"
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

    async def search_flights(self):
        """Search for delayed and cancelled flights (conservative mode)."""
        print(f"\n{'='*80}")
        print(f"CONSERVATIVE FLIGHT SEARCH (Max {MAX_API_CREDITS} credits)")
        print(f"{'='*80}\n")
        print(f"API Base URL: {config.AERODATABOX_BASE_URL}")
        print(f"Search period: Last {MAX_DAYS_SEARCH} days")
        print(f"Flight numbers to try: {len(HIGH_TRAFFIC_FLIGHTS)}")
        print(f"Max credits budget: {MAX_API_CREDITS} credits")
        print(f"Target: 3 flights per category (9 total)\n")

        if not config.AERODATABOX_API_KEY:
            print("❌ ERROR: AERODATABOX_API_KEY not configured")
            return

        today = date.today()

        # Search recent dates
        for days_ago in range(2, MAX_DAYS_SEARCH + 2):
            flight_date = today - timedelta(days=days_ago)
            flight_date_str = flight_date.strftime("%Y-%m-%d")

            # Check if we have enough flights
            if self._have_enough_flights():
                print(f"\n✅ Found enough flights! Stopping search.")
                break

            # Check credit limit
            if self.credits_used >= MAX_API_CREDITS:
                print(f"\n⚠️  Reached credit limit ({MAX_API_CREDITS}). Stopping search.")
                break

            print(f"\n📅 Date: {flight_date_str} ({days_ago} days ago)")

            # Try different flight numbers
            for airline_code, flight_num in HIGH_TRAFFIC_FLIGHTS:
                flight_number = f"{airline_code}{flight_num}"

                # Check limits before each call
                if self._have_enough_flights():
                    break

                if self.credits_used >= MAX_API_CREDITS:
                    print(f"\n⚠️  Reached credit limit. Stopping.")
                    break

                try:
                    found = await self._check_flight(flight_number, flight_date_str)

                    # Small delay to avoid rate limiting
                    if found:
                        await asyncio.sleep(0.3)

                except Exception:
                    continue

            # Progress update
            print(f"   Status: Under3h={len(self.flights_under_3h)}/3 | "
                  f"Over3h={len(self.flights_over_3h)}/3 | "
                  f"Cancelled={len(self.flights_cancelled)}/3 | "
                  f"Credits used: {self.credits_used}/{MAX_API_CREDITS}")

    def _have_enough_flights(self) -> bool:
        """Check if we have enough flights in each category."""
        return (len(self.flights_under_3h) >= 3 and
                len(self.flights_over_3h) >= 3 and
                len(self.flights_cancelled) >= 3)

    async def _check_flight(self, flight_number: str, flight_date: str) -> bool:
        """Check a specific flight. Returns True if flight data was found."""
        self.api_calls += 1

        try:
            url = f"{config.AERODATABOX_BASE_URL}/flights/number/{flight_number}/{flight_date}"

            async with httpx.AsyncClient(timeout=config.AERODATABOX_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 404:
                    return False  # Flight doesn't exist (no credits charged)

                if response.status_code != 200:
                    return False

                # Successfully got data - charge credits
                self.successful_calls += 1
                self.credits_used += 2  # TIER 2 = 2 credits

                # Parse JSON
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return False

                if not data:
                    return False

                # Parse flights
                flights = data if isinstance(data, list) else [data]

                for flight in flights:
                    flight_info = self._parse_flight_info(flight, flight_number, flight_date)

                    if not flight_info:
                        continue

                    # Categorize
                    if flight_info["is_cancelled"] and len(self.flights_cancelled) < 3:
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

        except Exception:
            return False

    def _parse_flight_info(self, flight: Dict[str, Any], flight_number: str,
                           flight_date: str) -> Dict[str, Any]:
        """Parse flight data from API response."""
        try:
            status = flight.get("status", "").lower()
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})

            dep_airport = departure.get("airport", {}).get("iata", "")
            arr_airport = arrival.get("airport", {}).get("iata", "")
            airline_name = flight.get("airline", {}).get("name", "")

            # Extract times
            scheduled_arrival_time = arrival.get("scheduledTime", {})
            actual_arrival_time = arrival.get("actualTime", {})
            scheduled_arrival = scheduled_arrival_time.get("utc") if scheduled_arrival_time else None
            actual_arrival = actual_arrival_time.get("utc") if actual_arrival_time else None

            # Calculate delay
            delay_minutes = None
            if scheduled_arrival and actual_arrival:
                try:
                    scheduled = datetime.fromisoformat(scheduled_arrival.replace('Z', '+00:00'))
                    actual = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
                    delay_minutes = int((actual - scheduled).total_seconds() / 60)

                    if delay_minutes < 0:
                        delay_minutes = None
                except Exception:
                    delay_minutes = None

            is_cancelled = status in ["cancelled", "canceled"]

            # Skip if no useful data or delay too small
            if not is_cancelled and not delay_minutes:
                return None
            if delay_minutes and delay_minutes < 30:
                return None

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

        except Exception:
            return None

    def print_results(self):
        """Print final results summary."""
        print(f"\n\n{'='*80}")
        print(f"SEARCH RESULTS")
        print(f"{'='*80}\n")
        print(f"Total API calls: {self.api_calls}")
        print(f"Successful calls: {self.successful_calls}")
        print(f"Credits used: {self.credits_used}/{MAX_API_CREDITS}")
        print(f"Flights found: {len(self.flights_under_3h) + len(self.flights_over_3h) + len(self.flights_cancelled)}/9\n")

        # Print results by category
        self._print_category("CANCELLED", self.flights_cancelled, "🔴")
        self._print_category("DELAYS > 3 HOURS", self.flights_over_3h, "🟠")
        self._print_category("DELAYS < 3 HOURS", self.flights_under_3h, "🟡")

        # Export to JSON
        output = {
            "cancelled": self.flights_cancelled,
            "delays_over_3h": self.flights_over_3h,
            "delays_under_3h": self.flights_under_3h,
            "metadata": {
                "total_flights_found": len(self.flights_under_3h) + len(self.flights_over_3h) + len(self.flights_cancelled),
                "api_calls": self.api_calls,
                "successful_calls": self.successful_calls,
                "credits_used": self.credits_used,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

        output_file = "real_delayed_flights.json"
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Results exported to: {output_file}")

        # Print usage summary
        remaining_credits = 600 - self.credits_used  # Assuming 600/month quota
        print(f"\n💰 API Usage Summary:")
        print(f"   Credits used: {self.credits_used}")
        print(f"   Monthly quota: 600")
        print(f"   Remaining: {remaining_credits} credits")
        print(f"   Usage: {(self.credits_used/600*100):.1f}% of monthly quota")

    def _print_category(self, title: str, flights: List[Dict], emoji: str):
        """Print flights in a category."""
        print(f"\n{emoji} {title} ({len(flights)}/3):")
        print(f"{'-'*80}")
        if flights:
            for flight in flights:
                print(f"  Flight: {flight['flight_number']}")
                print(f"  Route:  {flight['departure_airport']} → {flight['arrival_airport']}")
                print(f"  Date:   {flight['flight_date']}")
                print(f"  Airline: {flight['airline']}")
                if flight.get('delay_minutes'):
                    print(f"  Delay:  {flight['delay_minutes']} min ({flight['delay_minutes']/60:.1f}h)")
                else:
                    print(f"  Status: {flight['status'].upper()}")
                print()
        else:
            print("  None found\n")


async def main():
    """Main entry point."""
    finder = ConservativeFlightFinder()

    try:
        await finder.search_flights()
        finder.print_results()

    except KeyboardInterrupt:
        print("\n\n⚠️  Search interrupted")
        finder.print_results()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        finder.print_results()


if __name__ == "__main__":
    print(f"\n⚠️  CONSERVATIVE MODE")
    print(f"This script will use at most {MAX_API_CREDITS} API credits (~{MAX_API_CREDITS/600*100:.1f}% of monthly quota)")
    print(f"Searching last {MAX_DAYS_SEARCH} days for {len(HIGH_TRAFFIC_FLIGHTS)} high-traffic flights")
    print(f"\nPress Ctrl+C at any time to stop and see results so far.\n")

    asyncio.run(main())
