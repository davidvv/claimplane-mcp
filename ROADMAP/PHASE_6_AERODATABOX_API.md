# Phase 6: AeroDataBox Flight Status API Integration

[← Back to Roadmap](README.md)

---

**Priority**: HIGH
**Status**: 📋 **PLANNED**
**Estimated Effort**: 2-3 weeks
**Business Value**: Automates flight verification and improves accuracy
**Target Version**: v0.6.0
**API Provider**: AeroDataBox (https://aerodatabox.com/)
**API Tier**: Tier 2 (Flight Status API)
**Cost**: Free tier (300 calls/month) or $5/month (3,000 calls)

---

**API Documentation**: https://aerodatabox.com/

### Overview

Integrate AeroDataBox Flight Status API to automate flight verification and provide real-time flight delay/cancellation information. This eliminates manual flight verification work for admins and improves claim accuracy.

### Business Case

**Current Problem**:
- Admins manually verify flight delays using airline websites
- Time-consuming and error-prone process
- Cannot verify flight status in real-time
- Customers must provide delay certificates (extra friction)
- No automated eligibility pre-screening

**Solution**: AeroDataBox API integration providing:
- Automated flight delay/cancellation verification
- Real-time flight status during claim submission
- Historical flight data for past claims
- Airport information and distances (for EU261 compensation calculation)
- Reduced manual admin work

**Expected Impact**:
- **60-80% reduction** in flight verification time for admins
- **Higher claim accuracy** - automated data from authoritative source
- **Better customer experience** - instant eligibility check during submission
- **Reduced support tickets** - customers know eligibility upfront
- **Fraud prevention** - verify flight actually existed and was delayed

### Key Features

#### 6.1 Flight Verification Service

**File**: `app/services/flight_data_service.py` (new)

- [ ] **Flight Status Lookup**
  - Get real-time flight status (scheduled, delayed, cancelled, diverted)
  - Retrieve scheduled vs actual departure/arrival times
  - Calculate delay duration automatically
  - Support IATA and ICAO airport codes
  - Handle multiple flights per day (morning/evening flights with same number)

- [ ] **Historical Flight Data**
  - Query flights up to 12 months in the past
  - Retrieve delay/cancellation records for claims
  - Store flight data snapshot with claim (audit trail)

- [ ] **Airport Information**
  - Get airport details (name, city, country, coordinates)
  - Calculate great-circle distance between airports
  - Use for EU261 compensation tier calculation (< 1500km, 1500-3500km, > 3500km)

- [ ] **API Error Handling**
  - Rate limiting compliance (AeroDataBox has quotas)
  - Caching of flight data (reduce API calls)
  - Fallback to manual verification if API unavailable
  - Graceful degradation (don't block claims if API is down)

#### 6.2 Enhanced Claim Submission Flow

**Files**: `app/routers/claims.py`, `frontend_Claude45/src/pages/ClaimForm.tsx`

- [ ] **Real-Time Flight Lookup** during claim submission
  - Customer enters flight number and date
  - System automatically fetches flight details from AeroDataBox
  - Pre-populate flight times, airline, airports
  - Display delay duration and eligibility status
  - Show "Flight not found" or "Flight was on time" if ineligible

- [ ] **Smart Eligibility Pre-Screening**
  - Calculate delay duration from API data
  - Apply EU261 rules automatically
  - Show compensation estimate before submission
  - Warn if flight doesn't qualify (< 3 hour delay)
  - Reduce ineligible claim submissions by 40-50%

- [ ] **Flight Data Snapshot**
  - Store retrieved flight data with claim in database
  - Include: scheduled times, actual times, delay duration, cancellation status
  - Prevent data loss if API data changes later
  - Audit trail for legal compliance

#### 6.3 Admin Dashboard Enhancements

**Files**: `app/routers/admin_claims.py`, `frontend_Claude45/src/pages/Admin/ClaimDetailPage.tsx`

- [ ] **Automated Verification Badge**
  - Show "API Verified" badge on claims with flight data from AeroDataBox
  - Display flight details retrieved from API
  - Compare customer-entered data vs API data (flag discrepancies)
  - One-click re-verification for updated data

- [ ] **Manual Verification Fallback**
  - If API data unavailable, allow admin manual verification
  - Upload delay certificate as before
  - Mark verification method (API vs manual)

- [ ] **Flight Status Dashboard**
  - View all claims for a specific flight number
  - See how many passengers from one flight filed claims
  - Bulk processing for mass cancellations/delays

#### 6.4 Database Schema Updates

**File**: `app/models.py` (update)

Add new `FlightData` model:

```python
class FlightData(Base):
    __tablename__ = "flight_data"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(PGUUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)

    # Flight identification
    flight_number = Column(String(10), nullable=False)
    flight_date = Column(Date, nullable=False)
    airline_iata = Column(String(3), nullable=True)
    airline_name = Column(String(255), nullable=True)

    # Airports
    departure_airport_iata = Column(String(3), nullable=False)
    departure_airport_name = Column(String(255), nullable=True)
    arrival_airport_iata = Column(String(3), nullable=False)
    arrival_airport_name = Column(String(255), nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)

    # Scheduled times
    scheduled_departure = Column(DateTime(timezone=True), nullable=True)
    scheduled_arrival = Column(DateTime(timezone=True), nullable=True)

    # Actual times
    actual_departure = Column(DateTime(timezone=True), nullable=True)
    actual_arrival = Column(DateTime(timezone=True), nullable=True)

    # Status
    flight_status = Column(String(50), nullable=True)  # scheduled, delayed, cancelled, diverted
    delay_minutes = Column(Integer, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # API metadata
    api_source = Column(String(50), default="aerodatabox")  # aerodatabox, manual, other
    api_retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    api_response_raw = Column(JSON, nullable=True)  # Store full API response for audit

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### 6.5 Configuration Updates

**File**: `app/config.py` (update)

```python
# AeroDataBox API Configuration
AERODATABOX_API_KEY = os.getenv("AERODATABOX_API_KEY", "")
AERODATABOX_BASE_URL = os.getenv("AERODATABOX_BASE_URL", "https://api.aerodatabox.com/v1")
AERODATABOX_ENABLED = os.getenv("AERODATABOX_ENABLED", "false").lower() == "true"

# Flight data caching (reduce API calls)
FLIGHT_DATA_CACHE_HOURS = int(os.getenv("FLIGHT_DATA_CACHE_HOURS", "24"))
```

#### 6.6 Caching Strategy

**File**: `app/services/cache_service.py` (new or existing)

- [ ] Cache flight data for 24 hours (configurable)
- [ ] Key: `flight:{flight_number}:{flight_date}`
- [ ] Use Redis for distributed caching
- [ ] Automatic cache invalidation after expiry
- [ ] Manual cache refresh endpoint for admins

### API Pricing & Quotas

**AeroDataBox Pricing** (https://aerodatabox.com/pricing/):

Flight Status API is **Tier 2** pricing:
- **Free Tier**: 600 credits/month (300 API calls) - $0/month
- **Pro Tier 1**: 6,000 credits/month (3,000 API calls) - $5/month
- **Pro Tier 2**: 60,000 credits/month (30,000 API calls) - $50/month
- **Enterprise**: Custom pricing for higher volumes

**Note**: Each Tier 2 API call costs 2 credits = 1 API call

**Recommended Approach**:
- Start with **Free Tier** (300 calls/month) for MVP testing
- Upgrade to **Pro Tier 1** ($5/month, 3,000 calls) when launching
- Implement aggressive caching (reduce duplicate requests)
- Monitor usage and upgrade if needed
- Fallback to manual verification if quota exceeded

**Expected Usage**:
- Assume 100 claims/month initially
- With caching: ~100-150 API calls/month
- Free tier sufficient for initial testing
- Pro Tier 1 ($5/month) provides 20x headroom for growth
- Cost per claim: ~$0.05 (vs hours of manual work)

### Testing Requirements

- [ ] Test flight lookup with various airlines (Lufthansa, Ryanair, British Airways)
- [ ] Test historical flight data retrieval (6 months ago, 1 year ago)
- [ ] Test edge cases (cancelled flight, diverted flight, multiple flights per day)
- [ ] Test API error handling (rate limit, timeout, invalid flight)
- [ ] Test caching (verify no duplicate API calls)
- [ ] Test manual fallback when API unavailable
- [ ] Load testing (ensure caching reduces API calls)

### Success Criteria

- ✅ 90%+ of claims have automated flight verification
- ✅ Average verification time reduced from 5 minutes to < 30 seconds
- ✅ Flight distance automatically calculated for compensation tiers
- ✅ Customers see eligibility before submitting claim
- ✅ Ineligible claim submissions reduced by 40%+
- ✅ API cost < $5/month for first 200 claims/month (Pro Tier 1 sufficient)
- ✅ Graceful fallback to manual verification when API unavailable

### Dependencies

- **API Account**: AeroDataBox account (https://aerodatabox.com/)
- **Redis**: For caching (already in use for Celery)
- **Phase 1 Complete**: Admin dashboard must exist
- **Phase 3 Complete**: Authentication for API key security

### Open Questions

1. **API Provider**: AeroDataBox vs alternatives (Aviation Edge, FlightAware)?
   - Recommendation: AeroDataBox (good pricing, comprehensive data, reliable)

2. **Historical Data Limit**: How far back should we support claims?
   - Recommendation: 12 months (EU261 has 3-6 year statute depending on country, but most claims are within months)

3. **Manual Override**: Should admins be able to override API data?
   - Recommendation: Yes (API could be wrong, allow manual correction with audit log)

4. **Multi-Leg Flights**: How to handle connecting flights?
   - Future enhancement: Phase 5+ (requires complex eligibility logic)

---

## Phase 7: Payment System Integration

---

[← Back to Roadmap](README.md)
