# Phase 6.5: Flight Search by Route & Time

[← Back to Roadmap](README.md)

---

**Priority**: MEDIUM
**Status**: 📋 **PLANNED**
**Estimated Effort**: 3-5 days
**Business Value**: Reduces user friction, competitive advantage
**Target Version**: v0.6.1
**API Provider**: AeroDataBox (https://aerodatabox.com/) or alternative
**API Tier**: Tier 2 (Flight Status API - route search endpoint)
**Cost**: Shares Phase 6 quota - Free tier or $5/month
**Dependencies**: Phase 6 (shares infrastructure, but can use different provider)

---

## Overview

Enable customers to search for flights by route (departure/arrival airports) and approximate time when they don't know their flight number. This significantly improves UX and reduces abandonment during claim submission.

**Modularity Note**: This phase is designed to be independent from Phase 6. While they share the same default provider (AeroDataBox), the route search functionality can use a different API provider if needed without affecting Phase 6's flight number verification.

---

## Business Case

**Current Problem**:
- Users must know their exact flight number to submit a claim
- Many travelers don't remember flight numbers (only know route and approximate time)
- High abandonment rate during Step 1 of claim submission
- Users must go find boarding pass/confirmation email before starting claim
- Competitors require flight number (friction point)

**Solution**: Flight search by route
- User enters: Departure airport + Arrival airport + Date + Approximate time (optional)
- System returns: List of matching flights on that route
- User selects correct flight from list
- Normal flow continues with selected flight number

**Expected Impact**:
- **30-40% reduction** in Step 1 abandonment rate
- **Better conversion** - users can start claim immediately without documents
- **Competitive advantage** - most competitors don't offer route search
- **Improved UX** - flexible input methods accommodate different user contexts
- **Market research data** - understand popular routes for marketing

---

## Key Features

### 6.5.1 Route Search Service

**File**: `app/services/flight_search_service.py` (new)

- [ ] **Route Search API Integration**
  - Search flights by departure + arrival airport + date
  - Optional time range filtering (e.g., "morning flights", "around 14:00")
  - Support IATA codes (MUC, JFK) and airport names
  - Return list of flights sorted by departure time
  - Handle multiple pages of results (busy routes may have 50+ flights/day)

- [ ] **Result Filtering & Sorting**
  - Filter by time range if provided (± 3 hours from specified time)
  - Sort by departure time (ascending)
  - Filter out flights more than 12 months old (outside claim window)
  - Highlight delayed/cancelled flights (more likely to be eligible)

- [ ] **Airport Autocomplete Service**
  - Search airports by IATA code, name, or city
  - Return top 10 matches with IATA code, name, city, country
  - Cache popular airports for performance
  - Support fuzzy matching ("New York" → JFK, LGA, EWR)

- [ ] **Smart Caching**
  - Cache route search results by `{from}:{to}:{date}` for 24 hours
  - Separate cache namespace from Phase 6 (allows different TTLs)
  - Cache airport autocomplete data for 7 days
  - Implement cache warming for popular routes

- [ ] **API Error Handling**
  - Fallback to flight number input if route search fails
  - Show helpful error messages ("No flights found on this route")
  - Log search queries for analytics (track popular routes)
  - Graceful degradation (never block users from manual entry)

### 6.5.2 Enhanced Flight Input UI

**File**: `frontend_Claude45/src/pages/ClaimForm/Step1_Flight.tsx` (update)

- [ ] **Dual Input Mode Toggle**
  ```
  How would you like to find your flight?

  ○ I know my flight number
  ● I know my route and time
  ```

- [ ] **Route Search Form**
  - **Departure Airport**: Autocomplete input with IATA codes
    - As user types: "Mun" → shows "Munich (MUC)", "Münster (FMO)"
    - Display: "City (IATA) - Airport Name"
    - Validate: Must select from autocomplete (prevent invalid codes)

  - **Arrival Airport**: Same autocomplete behavior

  - **Date**: Date picker (same as existing flight number flow)

  - **Approximate Time** (Optional): Time input or dropdown
    - Options: "Morning (6am-12pm)", "Afternoon (12pm-6pm)", "Evening (6pm-12am)", or specific time
    - Help text: "Leave blank to see all flights on this day"

- [ ] **Search Results Display**
  - Card-based layout showing each matching flight:
    ```
    ┌────────────────────────────────────────────┐
    │ ✈ LH8960 - Lufthansa                      │
    │ Munich (MUC) → New York JFK (JFK)         │
    │ Dep: 13:45 | Arr: 17:20 EDT               │
    │ Status: Delayed 180 min ⚠️                │
    │ Compensation: €600                         │
    │ [Select This Flight] ←─────────────────── │
    └────────────────────────────────────────────┘
    ```

  - Show 5-10 results initially with "Load More" button
  - Highlight delayed/cancelled flights (eligible)
  - Show "On Time" flights with lower priority
  - If no results: "No flights found - try adjusting your search"

- [ ] **Flight Selection Flow**
  - User clicks "Select This Flight"
  - System auto-populates Step 1 with selected flight data
  - UI switches to "flight number mode" showing selected flight
  - User can go back and search again if wrong flight selected
  - Continue to Step 2 (normal flow)

### 6.5.3 Backend API Endpoints

**File**: `app/routers/flights.py` (new or update)

- [ ] **Airport Search Endpoint**
  ```python
  GET /api/flights/airports/search?query=munich

  Response:
  {
    "airports": [
      {
        "iata": "MUC",
        "name": "Munich Airport",
        "city": "Munich",
        "country": "Germany"
      },
      ...
    ]
  }
  ```

- [ ] **Route Search Endpoint**
  ```python
  GET /api/flights/search?from=MUC&to=JFK&date=2025-01-15&time=14:00

  Response:
  {
    "flights": [
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
        "actualDeparture": "2025-01-15T16:45:00+01:00",
        "actualArrival": "2025-01-15T20:20:00-05:00",
        "status": "delayed",
        "delayMinutes": 180,
        "distanceKm": 6200,
        "estimatedCompensation": 600
      },
      ...
    ],
    "total": 12,
    "page": 1,
    "perPage": 10
  }
  ```

- [ ] **Input Validation**
  - Validate IATA codes (3 letters, uppercase)
  - Validate date format and range (not in future, not > 12 months ago)
  - Validate time format if provided
  - Return 400 Bad Request for invalid inputs

### 6.5.4 Database Schema Updates

**File**: `app/models.py` (update - minimal changes)

**No new tables required!** Phase 6's `FlightData` model already stores all needed data.

Optional enhancement - track search analytics:

```python
class FlightSearchLog(Base):
    """Optional: Track route searches for analytics"""
    __tablename__ = "flight_search_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Search parameters
    departure_airport = Column(String(3), nullable=False)
    arrival_airport = Column(String(3), nullable=False)
    search_date = Column(Date, nullable=False)
    search_time = Column(String(10), nullable=True)  # e.g., "14:00" or "morning"

    # Results
    results_count = Column(Integer, nullable=False)
    selected_flight_number = Column(String(10), nullable=True)  # which flight user selected

    # Metadata
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Purpose**: Business intelligence - identify popular routes for marketing campaigns

### 6.5.5 Configuration Updates

**File**: `app/config.py` (update)

```python
# Flight Search Configuration (modular from Phase 6)
FLIGHT_SEARCH_ENABLED = os.getenv("FLIGHT_SEARCH_ENABLED", "false").lower() == "true"
FLIGHT_SEARCH_PROVIDER = os.getenv("FLIGHT_SEARCH_PROVIDER", "aerodatabox")  # aerodatabox, aviationstack, flightaware

# Provider-specific configs (allows switching providers)
if FLIGHT_SEARCH_PROVIDER == "aerodatabox":
    FLIGHT_SEARCH_API_KEY = os.getenv("AERODATABOX_API_KEY", "")
    FLIGHT_SEARCH_BASE_URL = os.getenv("AERODATABOX_BASE_URL", "https://api.aerodatabox.com/v1")
elif FLIGHT_SEARCH_PROVIDER == "aviationstack":
    FLIGHT_SEARCH_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")
    FLIGHT_SEARCH_BASE_URL = "http://api.aviationstack.com/v1"
# Add more providers as needed

# Search result limits
FLIGHT_SEARCH_MAX_RESULTS = int(os.getenv("FLIGHT_SEARCH_MAX_RESULTS", "50"))
FLIGHT_SEARCH_CACHE_HOURS = int(os.getenv("FLIGHT_SEARCH_CACHE_HOURS", "24"))

# Airport autocomplete
AIRPORT_AUTOCOMPLETE_CACHE_DAYS = int(os.getenv("AIRPORT_AUTOCOMPLETE_CACHE_DAYS", "7"))
```

### 6.5.6 Caching Strategy

**File**: `app/services/cache_service.py` (update)

- [ ] **Route Search Results Cache**
  - Key: `flight_search:{from}:{to}:{date}` (omit time to maximize cache hits)
  - TTL: 24 hours (configurable)
  - Store full flight list for route+date
  - Client-side filtering by time if needed

- [ ] **Airport Data Cache**
  - Key: `airport:{iata}` or `airports:search:{query}`
  - TTL: 7 days (airport data rarely changes)
  - Preload top 100 airports on startup

- [ ] **Cache Warming**
  - Background job: Pre-cache popular routes (e.g., MUC-JFK, LHR-JFK)
  - Triggered daily at 2am UTC
  - Reduces API calls for common searches

---

## API Provider Options

**Primary**: AeroDataBox (same as Phase 6)
- Endpoint: `/flights/{departure}/{arrival}/{date}`
- Returns all flights on route for specified date
- Pricing: Included in Phase 6 quota (Pro Plan $50/month)

**Alternative 1**: AviationStack
- Good fallback if AeroDataBox route search unavailable
- Endpoint: `/flights?dep_iata=MUC&arr_iata=JFK&flight_date=2025-01-15`
- Pricing: Free tier (100 requests/month), Paid plans from $10/month

**Alternative 2**: FlightAware AeroAPI
- Premium option with more comprehensive data
- Endpoint: `/airports/{id}/flights/scheduled`
- Pricing: Custom (enterprise)

**Recommended**: Start with AeroDataBox (consistent with Phase 6), design service layer to allow provider switching via config.

---

## API Pricing Impact

**AeroDataBox Pricing** (https://aerodatabox.com/pricing/):

Flight Status API is **Tier 2** pricing:
- **Free Tier**: 600 credits/month (300 API calls) - $0/month
- **Pro Tier 1**: 6,000 credits/month (3,000 API calls) - $5/month
- **Pro Tier 2**: 60,000 credits/month (30,000 API calls) - $50/month

**Note**: Each Tier 2 API call costs 2 credits = 1 API call

**AeroDataBox Route Search Usage**:
- Route search counts as 1 API call (regardless of # of flights returned)
- Estimate: 30% of users will use route search (70% know flight number)
- Expected usage: 30 route searches per 100 claims
- With caching: Reduce to ~20 unique route searches per 100 claims

**Combined Phase 6 + 6.5 Usage**:
- Phase 6: 100 flight lookups/month
- Phase 6.5: 20 route searches/month
- Total: ~120 API calls/month
- **Free Tier** (300 calls/month) sufficient for MVP testing
- **Pro Tier 1** ($5/month, 3,000 calls/month) provides 25x headroom
- Cost per claim: ~$0.05 with Pro Tier 1

---

## Testing Requirements

- [ ] **Frontend Tests**
  - Airport autocomplete behavior (typing, selection, validation)
  - Route search form validation (empty fields, invalid dates)
  - Search results rendering (empty, single, many results)
  - Flight selection flow (select, back, change)

- [ ] **API Integration Tests**
  - Route search with various airports (busy routes, rare routes)
  - Time filtering (morning, afternoon, evening, specific time)
  - Pagination (routes with 50+ flights/day)
  - Error handling (invalid airport, no results, API timeout)

- [ ] **Edge Cases**
  - Routes with no flights on specified date
  - Airports with multiple codes (NYC → JFK, LGA, EWR)
  - International date line crossings
  - Flights with same number but different routes (airline reuse)

- [ ] **Performance Tests**
  - Cache hit rate (should be > 60% for popular routes)
  - Search response time (< 2 seconds)
  - Autocomplete latency (< 500ms)
  - Concurrent searches (100 simultaneous users)

- [ ] **Provider Switching Test**
  - Switch config from AeroDataBox to AviationStack
  - Verify service layer adapter works correctly
  - Confirm data format consistency

---

## Success Criteria

- ✅ 30%+ of users successfully find flights via route search
- ✅ Step 1 abandonment rate reduced by 20%+
- ✅ Average search returns 5-15 relevant results
- ✅ 90%+ of route searches complete in < 3 seconds
- ✅ Cache hit rate > 60% for route searches
- ✅ Zero impact on Phase 6 flight number verification
- ✅ Can switch API provider via config change (no code changes)
- ✅ Combined API costs < $5/month for both Phase 6 + 6.5 (Pro Tier 1 sufficient)

---

## Dependencies

**Required**:
- **Phase 6 Infrastructure**: Shares Redis caching, flight data service patterns
- **Phase 3 Complete**: JWT auth for rate limiting per user
- **Frontend Step 1**: Existing flight input component to enhance

**Optional**:
- **Phase 6 FlightData Model**: Can reuse for storing selected flight data
- **Phase 6.5 can launch independently**: If Phase 6 is delayed, route search can use its own provider

---

## Implementation Strategy

### Option A: After Phase 6 (Recommended)
1. Complete Phase 6 (flight number verification)
2. Validate AeroDataBox integration works
3. Add route search endpoint to same service
4. Enhance frontend with dual input mode
5. Launch as incremental UX improvement

**Benefits**: Lower risk, proven API integration, shared infrastructure

### Option B: Parallel with Phase 6
1. Design both features together
2. Build unified flight service with two modes
3. Launch both simultaneously

**Benefits**: Faster time to market, unified UX from day 1

### Option C: Independent from Phase 6
1. Use different API provider (e.g., AviationStack)
2. Build separate service layer
3. Can launch before/after Phase 6

**Benefits**: No blocking dependencies, provider flexibility

---

## Migration Path (If Switching Providers)

If you decide to use a different provider for route search:

1. **Update Config**:
   ```python
   FLIGHT_SEARCH_PROVIDER = "aviationstack"  # Change from "aerodatabox"
   AVIATIONSTACK_API_KEY = "your_key_here"
   ```

2. **Implement Provider Adapter**:
   ```python
   # app/services/adapters/aviationstack_adapter.py
   class AviationStackAdapter(FlightSearchAdapter):
       def search_route(self, from_iata, to_iata, date):
           # Convert to AviationStack API format
           # Return standardized FlightSearchResult
   ```

3. **No Frontend Changes Required**: Service layer abstracts provider details

4. **Phase 6 Unaffected**: Flight number verification continues using AeroDataBox

---

## Open Questions

1. **Should we show flights that were on-time?**
   - Recommendation: Yes, but deprioritize them (show delayed flights first)
   - Reason: User might be wrong about delay, let them select any flight

2. **How many results to show initially?**
   - Recommendation: 10 flights with "Load More" button
   - Reason: Most routes have < 10 flights/day, keeps UI clean

3. **Should we allow ICAO codes (4 letters) in addition to IATA (3 letters)?**
   - Recommendation: Yes, but convert to IATA internally
   - Reason: Some users know ICAO (EDDM = MUC), increases accessibility

4. **Track search analytics for business intelligence?**
   - Recommendation: Yes, add `FlightSearchLog` table
   - Reason: Identify popular routes for targeted marketing campaigns

5. **Should approximate time be required or optional?**
   - Recommendation: Optional
   - Reason: Many users won't remember exact time, date alone is enough

---

## Future Enhancements (Post-v0.6.1)

- **Smart Suggestions**: "Did you mean Lufthansa LH8960?" based on ML
- **Recent Searches**: "You recently searched MUC → JFK"
- **Popular Routes**: Show trending routes on homepage
- **Multi-Leg Support**: Search connecting flights (Phase 5 integration)
- **Email Parsing**: "Forward your booking confirmation, we'll extract details"
- **Mobile App**: Voice input "I flew from Munich to New York yesterday"

---

[← Back to Roadmap](README.md)
