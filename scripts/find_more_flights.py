#!/usr/bin/env python3
"""
Search for more delayed/cancelled flights in early-mid December 2025.
This avoids the holiday period and targets normal operations when delays are common.

Current progress:
- Cancelled: 2/3 ✅
- Delays >3h: 0/3 ❌
- Delays <3h: 0/3 ❌

Max credits: 75 (to get the remaining 7 flights)
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

# Expanded list focusing on routes with frequent delays
FLIGHTS_TO_CHECK = [
    # British Airways
    ("BA", "303"), ("BA", "304"), ("BA", "475"), ("BA", "476"),
    ("BA", "903"), ("BA", "904"), ("BA", "117"), ("BA", "118"),

    # Lufthansa
    ("LH", "400"), ("LH", "401"), ("LH", "110"), ("LH", "111"),

    # Air France (historically has delays)
    ("AF", "1216"), ("AF", "1217"), ("AF", "1518"), ("AF", "1519"),

    # KLM
    ("KL", "1000"), ("KL", "1001"),

    # Budget airlines (higher delay rates)
    ("FR", "166"), ("FR", "8"), ("FR", "1432"), ("FR", "9"),
    ("U2", "8321"), ("U2", "2085"), ("U2", "8"),
]

# Search early-mid December (normal operations, before holidays)
SEARCH_START_DATE = "2025-12-05"  # Dec 5
SEARCH_END_DATE = "2025-12-15"    # Dec 15
MAX_CREDITS = 75


class FlightFinder:
    def __init__(self, existing_data_file: str = "real_delayed_flights.json"):
        """Load existing flights and continue searching."""
        self.flights_under_3h = []
        self.flights_over_3h = []
        self.flights_cancelled = []
        self.api_calls = 0
        self.successful_calls = 0
        self.credits_used = 0
        self.headers = self._get_headers()

        # Load existing data
        self._load_existing_data(existing_data_file)

    def _load_existing_data(self, filepath: str):
        """Load previously found flights."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.flights_cancelled = data.get("cancelled", [])
                self.flights_over_3h = data.get("delays_over_3h", [])
                self.flights_under_3h = data.get("delays_under_3h", [])

                print(f"✅ Loaded existing data:")
                print(f"   Cancelled: {len(self.flights_cancelled)}/3")
                print(f"   Delays >3h: {len(self.flights_over_3h)}/3")
                print(f"   Delays <3h: {len(self.flights_under_3h)}/3")
                print()
        except FileNotFoundError:
            print("ℹ️  No existing data found, starting fresh\n")

    def _get_headers(self) -> Dict[str, str]:
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

    async def search_flights(self):
        """Search for flights in early-mid December."""
        print(f"{'='*80}")
        print(f"SEARCHING EARLY-MID DECEMBER 2025 (Normal Operations)")
        print(f"{'='*80}\n")
        print(f"Search period: {SEARCH_START_DATE} to {SEARCH_END_DATE}")
        print(f"Max credits: {MAX_CREDITS}")
        print(f"Target: 9 flights total (3 per category)\n")

        # Parse dates
        start = datetime.strptime(SEARCH_START_DATE, "%Y-%m-%d").date()
        end = datetime.strptime(SEARCH_END_DATE, "%Y-%m-%d").date()

        # Iterate through dates
        current_date = start
        while current_date <= end:
            flight_date_str = current_date.strftime("%Y-%m-%d")

            # Check limits
            if self._have_enough_flights():
                print(f"\n✅ Found all flights! Stopping.")
                break

            if self.credits_used >= MAX_CREDITS:
                print(f"\n⚠️  Credit limit reached ({MAX_CREDITS}). Stopping.")
                break

            print(f"\n📅 {flight_date_str}")

            # Try flights on this date
            for airline_code, flight_num in FLIGHTS_TO_CHECK:
                if self._have_enough_flights() or self.credits_used >= MAX_CREDITS:
                    break

                flight_number = f"{airline_code}{flight_num}"

                try:
                    found = await self._check_flight(flight_number, flight_date_str)
                    if found:
                        await asyncio.sleep(0.2)  # Rate limiting
                except Exception:
                    continue

            # Progress
            print(f"   Progress: Cancelled={len(self.flights_cancelled)}/3 | "
                  f">3h={len(self.flights_over_3h)}/3 | "
                  f"<3h={len(self.flights_under_3h)}/3 | "
                  f"Credits: {self.credits_used}/{MAX_CREDITS}")

            current_date += timedelta(days=1)

    def _have_enough_flights(self) -> bool:
        return (len(self.flights_under_3h) >= 3 and
                len(self.flights_over_3h) >= 3 and
                len(self.flights_cancelled) >= 3)

    async def _check_flight(self, flight_number: str, flight_date: str) -> bool:
        self.api_calls += 1

        try:
            url = f"{config.AERODATABOX_BASE_URL}/flights/number/{flight_number}/{flight_date}"

            async with httpx.AsyncClient(timeout=config.AERODATABOX_TIMEOUT) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code != 200:
                    return False

                self.successful_calls += 1
                self.credits_used += 2

                data = response.json()
                if not data:
                    return False

                flights = data if isinstance(data, list) else [data]

                for flight in flights:
                    flight_info = self._parse_flight_info(flight, flight_number, flight_date)
                    if not flight_info:
                        continue

                    # Check if we already have this flight
                    if self._is_duplicate(flight_info):
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
                            print(f"   🟡 <3h: {flight_info['display_name']} ({flight_info['delay_minutes']}min)")
                            return True

                        elif delay_hours >= 3 and len(self.flights_over_3h) < 3:
                            self.flights_over_3h.append(flight_info)
                            print(f"   🔴 >3h: {flight_info['display_name']} ({flight_info['delay_minutes']}min)")
                            return True

                return False

        except Exception:
            return False

    def _is_duplicate(self, flight_info: Dict[str, Any]) -> bool:
        """Check if this flight is already in our lists."""
        key = f"{flight_info['flight_number']}_{flight_info['flight_date']}"

        for flights_list in [self.flights_cancelled, self.flights_over_3h, self.flights_under_3h]:
            for existing in flights_list:
                existing_key = f"{existing['flight_number']}_{existing['flight_date']}"
                if key == existing_key:
                    return True
        return False

    def _parse_flight_info(self, flight: Dict[str, Any], flight_number: str,
                           flight_date: str) -> Dict[str, Any]:
        try:
            status = flight.get("status", "").lower()
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})

            dep_airport = departure.get("airport", {}).get("iata", "")
            arr_airport = arrival.get("airport", {}).get("iata", "")
            airline_name = flight.get("airline", {}).get("name", "")

            scheduled_arrival_time = arrival.get("scheduledTime", {})
            actual_arrival_time = arrival.get("actualTime", {})
            scheduled_arrival = scheduled_arrival_time.get("utc") if scheduled_arrival_time else None
            actual_arrival = actual_arrival_time.get("utc") if actual_arrival_time else None

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
        print(f"\n\n{'='*80}")
        print(f"FINAL RESULTS")
        print(f"{'='*80}\n")
        print(f"API calls: {self.api_calls}")
        print(f"Credits used: {self.credits_used}/{MAX_CREDITS}")
        print(f"Flights found: {len(self.flights_under_3h) + len(self.flights_over_3h) + len(self.flights_cancelled)}/9\n")

        # Print all categories
        for title, flights, emoji in [
            ("CANCELLED", self.flights_cancelled, "❌"),
            ("DELAYS > 3 HOURS", self.flights_over_3h, "🔴"),
            ("DELAYS < 3 HOURS", self.flights_under_3h, "🟡"),
        ]:
            print(f"{emoji} {title} ({len(flights)}/3):")
            print("-" * 80)
            if flights:
                for f in flights:
                    print(f"  {f['flight_number']}: {f['departure_airport']}→{f['arrival_airport']} on {f['flight_date']}")
                    if f.get('delay_minutes'):
                        print(f"    Delay: {f['delay_minutes']}min ({f['delay_minutes']/60:.1f}h)")
                    print()
            else:
                print("  None\n")

        # Export
        output = {
            "cancelled": self.flights_cancelled,
            "delays_over_3h": self.flights_over_3h,
            "delays_under_3h": self.flights_under_3h,
            "metadata": {
                "total_flights_found": len(self.flights_under_3h) + len(self.flights_over_3h) + len(self.flights_cancelled),
                "api_calls": self.api_calls,
                "successful_calls": self.successful_calls,
                "credits_used": self.credits_used,
                "generated_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat()
            }
        }

        with open("real_delayed_flights.json", "w") as f:
            json.dump(output, f, indent=2)

        print(f"✅ Saved to: real_delayed_flights.json")
        print(f"\n💰 Credits used: {self.credits_used} ({self.credits_used/600*100:.1f}% of monthly quota)")


async def main():
    finder = FlightFinder()

    try:
        await finder.search_flights()
        finder.print_results()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        finder.print_results()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        finder.print_results()


if __name__ == "__main__":
    print(f"\n🎯 Searching early-mid December for normal operations")
    print(f"   Current progress will be loaded and continued")
    print(f"   Max credits: {MAX_CREDITS}\n")
    asyncio.run(main())
