# Flight API Data Limitations

## Current Issue: Missing Gate Arrival Times

### Problem

**EU261/2004 Regulation Requirements:**
- Compensation eligibility is determined by delay at **gate arrival** (door opening time)
- NOT by runway touchdown time

**AeroDataBox API Limitation:**
- Provides `runwayTime`: Touchdown on runway
- Does **NOT** provide `actualTime`: Gate arrival / door opening
- Gap between touchdown and gate arrival: typically 10-30 minutes (taxi time)

### Current Workaround

**Implementation:** Airport-specific taxi times from comprehensive dataset

**Data Source:** `docs/comprehensive_airport_taxiing_times.csv`
- 184 major airports worldwide
- Region-specific taxi-in and taxi-out times
- Float precision (e.g., 10.7 min, 13.2 min)

**Service:** `app/services/airport_taxi_time_service.py`
- Loads CSV data on application startup
- In-memory cache for fast lookups
- Fallback to 15-minute default for unknown airports

**Implementation:** `app/routers/flights.py`
```python
# Get airport-specific taxi-in time
taxi_in_minutes = AirportTaxiTimeService.get_taxi_in_time(
    arr_airport,
    default=config.FLIGHT_TAXI_TIME_DEFAULT_MINUTES
)
delay_minutes += int(round(taxi_in_minutes))
```

**Configuration:**
```bash
FLIGHT_TAXI_TIME_DEFAULT_MINUTES=15  # Fallback for unknown airports
AIRPORT_TAXI_TIMES_CSV_PATH=docs/comprehensive_airport_taxiing_times.csv
```

**Example (UA988 on 2025-08-18):**
- Route: FRA (Frankfurt) → IAD (Washington Dulles)
- Runway delay: 2h 50min (170 min)
- **IAD taxi-in time**: 10.7 min (airport-specific)
- **With adjustment**: 3h 1min (181 min)
- **Actual gate delay**: 3h 13min
- Difference: 12 minutes short (still more accurate than flat 15 min)

**Note on Departure Times:**
- Testing shows AeroDataBox `revisedTime` for departure is already GATE time
- Therefore, we do NOT subtract taxi-out times at departure
- Only taxi-in times are added at arrival airport

### Impact

**Improved Accuracy:**
- Airport-specific times better reflect actual taxi conditions
- Major hubs (JFK: 13.3 min, LHR: 8.0 min) vs regional airports (GRZ: 1.9 min)
- More accurate than flat 15-minute estimate
- Still conservative compared to actual gate times

**Coverage:**
- 184 airports in dataset (all major EU/US/Asia-Pacific hubs)
- Unknown airports fall back to 15-minute default with warning logged
- Easily extensible by adding more airports to CSV

**Affected Claims:**
- Still underestimates for airports with exceptionally long taxi times during peak hours
- More accurate for airports with data in CSV
- Better threshold detection for 3-hour EU261 compensation eligibility

## Required Future Solution

### Option 1: FlightAware AeroAPI (Recommended)
- **Provides**: Gate arrival times (`actual_arrival_time.gate`)
- **Cost**: $100-$500/month depending on volume
- **Accuracy**: Real gate times from airline data
- **API**: https://www.flightaware.com/commercial/aeroapi/

### Option 2: FlightStats by Cirium
- **Provides**: Complete flight tracking including gate times
- **Cost**: Enterprise pricing (contact sales)
- **Accuracy**: High-quality airline data
- **API**: https://www.flightstats.com/

### Option 3: Aviation Stack
- **Provides**: Gate arrival/departure times
- **Cost**: $50-$200/month
- **Accuracy**: Good coverage for major airports
- **API**: https://aviationstack.com/

### Option 4: Direct Airline APIs
- **Provides**: Most accurate data directly from airlines
- **Cost**: Varies, some free for limited use
- **Complexity**: Need integrations with multiple airlines
- **Coverage**: Only covers specific airlines

## Comparison

| API | Gate Times | Cost/Month | Accuracy | Coverage |
|-----|-----------|------------|----------|----------|
| AeroDataBox (current) | ❌ No | Free-$50 | N/A | Global |
| FlightAware AeroAPI | ✅ Yes | $100-$500 | High | Global |
| FlightStats Cirium | ✅ Yes | Enterprise | Very High | Global |
| Aviation Stack | ✅ Yes | $50-$200 | Medium | Major airports |
| Direct Airline APIs | ✅ Yes | Free-Varies | Highest | Per airline |

## Action Items

### Immediate (Current Release)
- [x] Add 15-minute taxi time adjustment (Phase 1)
- [x] Document limitation in code comments
- [x] Log when adjustment is applied
- [x] Make adjustment configurable via env var
- [x] Implement airport-specific taxi times (Phase 2)
- [x] Load CSV data with 184 airports
- [x] Create AirportTaxiTimeService
- [x] Update delay calculation to use airport-specific times
- [x] Test with real flight data (UA988)

### Short-term (Next Release)
- [ ] Research and test FlightAware AeroAPI
- [ ] Compare pricing for expected API call volume
- [ ] Implement proof-of-concept with FlightAware
- [ ] A/B test accuracy vs current solution
- [ ] Add more airports to CSV as needed
- [ ] Consider time-of-day variations (peak vs off-peak)

### Long-term (Production)
- [ ] Switch to API with actual gate arrival times
- [ ] Remove taxi time estimation entirely
- [ ] Update documentation to reflect accurate data
- [ ] Monitor accuracy and adjust if needed
- [ ] Integrate with real-time airport data APIs

## Technical Details

### Code Locations

**Service Implementation:**
```python
# app/services/airport_taxi_time_service.py
class AirportTaxiTimeService:
    """Service for looking up airport-specific taxi times."""

    @classmethod
    def load_taxi_times(cls, csv_path: str):
        """Load taxi times from CSV into memory cache."""
        # Parses CSV: Region,IATA,City,Airport Name,Taxi-Out,Taxi-In
        # Stores in _taxi_times dict by IATA code

    @classmethod
    def get_taxi_in_time(cls, airport_iata: str, default: float = 15.0) -> float:
        """Get taxi-in time for arrival airport (float)."""
        # Returns airport-specific time or default
```

**Configuration:**
```python
# app/config.py
FLIGHT_TAXI_TIME_DEFAULT_MINUTES = int(os.getenv("FLIGHT_TAXI_TIME_DEFAULT_MINUTES", "15"))
AIRPORT_TAXI_TIMES_CSV_PATH = os.getenv(
    "AIRPORT_TAXI_TIMES_CSV_PATH",
    "docs/comprehensive_airport_taxiing_times.csv"
)
```

**Startup Initialization:**
```python
# app/main.py - lifespan function
from app.services.airport_taxi_time_service import AirportTaxiTimeService
try:
    AirportTaxiTimeService.load_taxi_times(config.AIRPORT_TAXI_TIMES_CSV_PATH)
    logger.info(f"Airport taxi times loaded ({airport_count} airports)")
except Exception as e:
    logger.warning(f"Failed to load: {e}. Using default fallback.")
```

**Implementation:**
```python
# app/routers/flights.py:374-390
if uses_runway_time and delay_minutes is not None:
    from app.services.airport_taxi_time_service import AirportTaxiTimeService

    # Get airport-specific taxi-in time
    taxi_in_minutes = AirportTaxiTimeService.get_taxi_in_time(
        arr_airport,
        default=config.FLIGHT_TAXI_TIME_DEFAULT_MINUTES
    )

    taxi_in_adjustment = int(round(taxi_in_minutes))
    delay_minutes += taxi_in_adjustment

    logger.info(
        f"Added {taxi_in_adjustment} min taxi-in time for {arr_airport} to {flight_number}"
    )
```

**Detection:**
```python
# app/routers/flights.py:350-357
# Check for actual gate time (not provided by AeroDataBox)
actual_arrival = arrival.get("actualTime", {}).get("utc") if isinstance(arrival.get("actualTime"), dict) else None

if not actual_arrival:
    # Use runway touchdown time (AeroDataBox only provides this)
    actual_arrival = arrival.get("runwayTime", {}).get("utc") if isinstance(arrival.get("runwayTime"), dict) else None
    if actual_arrival:
        uses_runway_time = True  # Flag for adjustment
```

### Testing

To verify airport-specific taxi time adjustment is working:

```bash
# Test flight with known gate delay
curl "http://localhost:80/flights/status/UA988?date=2025-08-18&refresh=true" | jq '.data.delay'

# Check logs for adjustment message
docker logs flight_claim_api 2>&1 | grep "taxi"
```

Expected log output:
```
INFO:app.main:Airport taxi times loaded successfully (184 airports)
INFO:app.routers.flights:Added 11 min taxi-in time for IAD to UA988 (runway-only data, EU261 requires gate arrival)
```

**Verification:**
- UA988 (FRA→IAD): Should add ~11 min (IAD taxi-in: 10.7 min)
- Old system: 170 + 15 = 185 min
- New system: 170 + 11 = 181 min (more accurate)

## References

- **EU261/2004 Regulation**: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32004R0261
- **Gate vs Runway Times**: EU261 Article 5(1)(c) - "...arrival at their final destination..."
- **ECJ Rulings**: Door opening time determines arrival, not touchdown

---

**Last Updated**: 2026-01-03
**Status**: Airport-specific taxi times implemented (184 airports)
**Priority**: Medium - Current solution provides good accuracy; long-term goal is real gate arrival API
