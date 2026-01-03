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

### Current Workaround (TEMPORARY)

**Implementation:** `app/routers/flights.py` and `app/config.py`

```python
# Add estimated taxi time to runway touchdown
delay_minutes += config.FLIGHT_TAXI_TIME_MINUTES  # Default: 15 minutes
```

**Configuration:**
```bash
FLIGHT_TAXI_TIME_MINUTES=15  # Adjustable via environment variable
```

**Example:**
- Flight: UA988 on 2025-08-18
- Runway delay: 2h 50min (170 min)
- **With adjustment**: 3h 5min (185 min)
- **Actual gate delay**: 3h 13min
- Difference: 8 minutes short (actual taxi time was ~23 min)

### Impact

**Conservative Estimate:**
- 15-minute average underestimates delays for flights with longer taxi times
- May show some eligible flights as ineligible
- Better than nothing, but not accurate

**Affected Claims:**
- Flights with delays close to 3-hour threshold (180 minutes)
- Example: Runway delay of 2h 50min might be eligible if actual gate delay > 3h
- Our estimate (3h 5min) shows eligible, but underestimates compensation period

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
- [x] Add 15-minute taxi time adjustment
- [x] Document limitation in code comments
- [x] Log when adjustment is applied
- [x] Make adjustment configurable via env var

### Short-term (Next Release)
- [ ] Research and test FlightAware AeroAPI
- [ ] Compare pricing for expected API call volume
- [ ] Implement proof-of-concept with FlightAware
- [ ] A/B test accuracy vs current solution

### Long-term (Production)
- [ ] Switch to API with actual gate arrival times
- [ ] Remove taxi time estimation
- [ ] Update documentation to reflect accurate data
- [ ] Monitor accuracy and adjust if needed

## Technical Details

### Code Locations

**Configuration:**
```python
# app/config.py
FLIGHT_TAXI_TIME_MINUTES = int(os.getenv("FLIGHT_TAXI_TIME_MINUTES", "15"))
```

**Implementation:**
```python
# app/routers/flights.py:371-379
if uses_runway_time and delay_minutes is not None:
    delay_minutes += config.FLIGHT_TAXI_TIME_MINUTES
    logger.info(
        f"Added {config.FLIGHT_TAXI_TIME_MINUTES} min taxi time to {flight_number} "
        f"(runway-only data, EU261 requires gate arrival)"
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

To verify taxi time adjustment is working:

```bash
# Test flight with known gate delay
curl "http://localhost:80/flights/status/UA988?date=2025-08-18&refresh=true" | jq '.data.delay'

# Check logs for adjustment message
docker logs flight_claim_api 2>&1 | grep "taxi time"
```

Expected log output:
```
INFO:app.routers.flights:Added 15 min taxi time to UA988 (runway-only data, EU261 requires gate arrival)
```

## References

- **EU261/2004 Regulation**: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32004R0261
- **Gate vs Runway Times**: EU261 Article 5(1)(c) - "...arrival at their final destination..."
- **ECJ Rulings**: Door opening time determines arrival, not touchdown

---

**Last Updated**: 2026-01-03
**Status**: Temporary workaround in place
**Priority**: High - Find production-ready solution before public launch
