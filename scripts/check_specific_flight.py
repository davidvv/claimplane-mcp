
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.aerodatabox_service import aerodatabox_service
from app.config import config

async def check_flight():
    # Force enable for this test
    config.AERODATABOX_ENABLED = True
    
    flight_number = "UA988"
    flight_date = "2025-08-18"
    
    print(f"Checking flight {flight_number} on {flight_date}...")
    try:
        result = await aerodatabox_service.get_flight_status(flight_number, flight_date)
        print("Flight status result:")
        import json
        print(json.dumps(result, indent=2))
        
        # Check departures/arrivals
        if isinstance(result, list):
            for flight in result:
                dep = flight.get("departure", {}).get("airport", {}).get("iata")
                arr = flight.get("arrival", {}).get("airport", {}).get("iata")
                print(f"Found flight: {dep} -> {arr}")
        elif isinstance(result, dict):
             # Some API responses might be a single dict or have a different structure
             print("Result is a dict, checking content...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_flight())
