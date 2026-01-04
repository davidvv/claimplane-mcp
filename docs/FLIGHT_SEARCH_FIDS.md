# Flight Search Using FIDS Endpoint

## Overview

This document describes the FIDS (Flight Information Display System) based flight search implementation, which provides an alternative to direct route search.

## Background

The AeroDataBox API does not provide a direct "Origin-to-Destination" search endpoint for some subscription tiers. Instead, we use the FIDS endpoint which:

1. Fetches **all departures** from an origin airport for a 24-hour window
2. Includes destination data when `withLeg=true` parameter is set
3. Allows local filtering by destination airport and airline

## Implementation

### New Methods in `AeroDataBoxService`

#### 1. `get_airport_departures()`

Low-level method that calls the FIDS endpoint.

```python
async def get_airport_departures(
    self,
    origin_icao: str,
    from_local: str,
    to_local: str
) -> Dict[str, Any]
```

**Endpoint:** `GET /flights/airports/icao/{icao}/{fromLocal}/{toLocal}?withLeg=true&direction=Departure`

**Parameters:**
- `origin_icao`: Origin airport ICAO code (e.g., "EDDM" for Munich)
- `from_local`: Start of time window (ISO format: "2025-01-15T00:00")
- `to_local`: End of time window (ISO format: "2025-01-15T23:59")

**Returns:** Raw API response with all departing flights

**API Tier:** TIER_2 (2 credits per call)

**Example:**
```python
from app.services.aerodatabox_service import aerodatabox_service

result = await aerodatabox_service.get_airport_departures(
    origin_icao="EDDM",
    from_local="2025-01-15T00:00",
    to_local="2025-01-15T23:59"
)
```

#### 2. `find_flights_by_route()`

High-level method that combines FIDS endpoint with local filtering.

```python
async def find_flights_by_route(
    self,
    origin_icao: str,
    destination_icao: str,
    departure_date: str,
    airline_iata: Optional[str] = None
) -> list[Dict[str, Any]]
```

**Parameters:**
- `origin_icao`: Origin airport ICAO code (4 letters)
- `destination_icao`: Destination airport ICAO code (4 letters)
- `departure_date`: Departure date (YYYY-MM-DD format)
- `airline_iata`: Optional airline IATA code for filtering (e.g., "LH", "DL", "UAL")

**Returns:** List of matching flight dictionaries with standardized fields

**Filtering Logic:**
1. Fetches all departures from origin airport (24-hour window)
2. Filters by `arrival.airport.icao` matching `destination_icao`
3. If `airline_iata` specified, filters by `airline.iata` matching `airline_iata`
4. Returns clean list of matching flights

**Example:**
```python
from app.services.aerodatabox_service import aerodatabox_service

# Find all Lufthansa flights from Munich to JFK
flights = await aerodatabox_service.find_flights_by_route(
    origin_icao="EDDM",
    destination_icao="KJFK",
    departure_date="2025-01-15",
    airline_iata="LH"
)

# Find ALL flights (any airline)
all_flights = await aerodatabox_service.find_flights_by_route(
    origin_icao="EDDM",
    destination_icao="KJFK",
    departure_date="2025-01-15",
    airline_iata=None  # No airline filter
)
```

#### 3. `findFlightsByRoute()` - Convenience Function

Standalone function with exact signature as requested.

```python
async def findFlightsByRoute(
    originIcao: str,
    destinationIcao: str,
    departureDate: str,
    airlineIata: str
) -> list[Dict[str, Any]]
```

This is a convenience wrapper around `AeroDataBoxService.find_flights_by_route()`.

**Example:**
```python
from app.services.aerodatabox_service import findFlightsByRoute

flights = await findFlightsByRoute(
    originIcao="EDDM",
    destinationIcao="KJFK",
    departureDate="2025-01-15",
    airlineIata="LH"
)

for flight in flights:
    print(f"{flight['flightNumber']}: {flight['scheduledDeparture']}")
```

## Response Format

Each flight object in the returned list contains:

```python
{
    "flightNumber": "LH8960",                        # Flight number
    "airline": "Lufthansa",                          # Airline name
    "airlineIata": "LH",                             # Airline IATA code
    "departureAirport": "EDDM",                      # Origin ICAO
    "arrivalAirport": "KJFK",                        # Destination ICAO
    "scheduledDeparture": "2025-01-15T13:45:00Z",   # ISO 8601 UTC
    "scheduledArrival": "2025-01-15T17:20:00Z",     # ISO 8601 UTC
    "actualDeparture": "2025-01-15T16:45:00Z",      # If available
    "actualArrival": "2025-01-15T20:20:00Z",        # If available
    "status": "delayed",                             # Flight status
    "delayMinutes": 180                              # Delay in minutes (if applicable)
}
```

## Error Handling

All methods use the existing AeroDataBox error handling:

- **Automatic retry** with exponential backoff for transient errors
- **Error classification** (retryable vs permanent)
- **Graceful degradation** (returns empty list instead of throwing on 404)

**Exception Types:**
- `AeroDataBoxClientError` - Invalid input (ICAO code, date format)
- `AeroDataBoxFlightNotFoundError` - No departures found (handled gracefully)
- `AeroDataBoxAuthenticationError` - API key issues
- `AeroDataBoxRateLimitError` - Rate limit exceeded
- `AeroDataBoxServerError` - Server-side errors (retryable)

**Example with error handling:**
```python
from app.services.aerodatabox_service import findFlightsByRoute
from app.exceptions import AeroDataBoxError

try:
    flights = await findFlightsByRoute("EDDM", "KJFK", "2025-01-15", "LH")

    if not flights:
        print("No flights found on this route")
    else:
        print(f"Found {len(flights)} flights")

except AeroDataBoxError as e:
    print(f"API error: {e}")
```

## Time Window Calculation

The function automatically calculates a 24-hour window:

```python
# For departure_date = "2025-01-15"
from_local = "2025-01-15T00:00"  # Start of day
to_local = "2025-01-15T23:59"    # End of day
```

**Note:** Currently uses UTC time for simplicity. In production, you may want to use the airport's local timezone for more accurate results.

## API Costs

- **FIDS Endpoint:** TIER_2 = 2 credits per call
- **One call per route search** (regardless of number of flights found)
- **Quota tracking:** Automatically tracked via `QuotaTrackingService`

## ICAO vs IATA Codes

### ICAO Codes (4 letters)
- Used for airports in this implementation
- Examples: EDDM (Munich), KJFK (JFK), EDDF (Frankfurt), KEWR (Newark)
- More precise and globally unique

### IATA Codes (3 letters)
- Used for airlines in this implementation
- Examples: LH (Lufthansa), UA (United), DL (Delta), BA (British Airways)
- Commonly used in consumer-facing flight numbers

**Conversion:**
If you need to convert IATA airport codes to ICAO, use:
```python
from app.services.airport_database_service import AirportDatabaseService

airports = AirportDatabaseService.search("MUC", limit=1)
if airports:
    icao = airports[0]["icao"]  # "EDDM"
```

## Testing

### Test Script
Run the FIDS endpoint test script to verify API behavior:

```bash
# Local
python scripts/test_fids_endpoint.py

# Docker
docker exec flight_claim_api python scripts/test_fids_endpoint.py
```

### Example Usage
Run the example script to see the function in action:

```bash
# Local
python scripts/example_find_flights_by_route.py

# Docker
docker exec flight_claim_api python scripts/example_find_flights_by_route.py
```

## Integration with Existing Code

This implementation is **compatible** with the existing route search infrastructure:

- Uses the same `AeroDataBoxService` HTTP client
- Shares quota tracking and caching infrastructure
- Returns standardized flight objects compatible with existing schemas
- Can be used as an **alternative** to the direct route endpoint

### When to Use FIDS vs Direct Route Endpoint

**Use FIDS (`find_flights_by_route`):**
- When direct route endpoint is not available in your API tier
- When you need flexibility to filter by airline after fetching
- When searching for all airlines on a route

**Use Direct Route (`AeroDataBoxRouteAdapter`):**
- When you have access to `/flights/{from}/{to}/{date}` endpoint
- When API costs are a concern (FIDS may return more data than needed)
- When you only need flights for a specific route

## Future Enhancements

Potential improvements:

1. **Timezone Support:** Use airport local timezone instead of UTC for time windows
2. **Caching:** Cache FIDS results and filter locally for different airlines
3. **Multi-day Search:** Extend to search across multiple days
4. **Advanced Filtering:** Add filters for departure time ranges, aircraft type, etc.

## References

- AeroDataBox API Documentation: [aerodatabox.com](https://www.aerodatabox.com)
- FIDS Endpoint: `GET /flights/airports/icao/{icao}/{fromLocal}/{toLocal}`
- Implementation: `app/services/aerodatabox_service.py`

## Support

For issues or questions:
1. Check the test script output: `scripts/test_fids_endpoint.py`
2. Review API response structure in logs
3. Verify ICAO codes are correct (4 letters)
4. Check API quota availability via `QuotaTrackingService`
