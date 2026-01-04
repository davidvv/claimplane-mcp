"""Pydantic schemas for flight data API responses."""
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AirportInfoSchema(BaseModel):
    """Airport information from AeroDataBox API."""

    iata: str = Field(..., description="IATA airport code (e.g., 'JFK')")
    icao: Optional[str] = Field(None, description="ICAO airport code")
    name: str = Field(..., description="Airport name")
    shortName: Optional[str] = Field(None, description="Short airport name")
    municipalityName: Optional[str] = Field(None, description="City/municipality name")
    location: Dict[str, Any] = Field(..., description="Location with lat/lon coordinates")
    countryCode: Optional[str] = Field(None, description="ISO country code")

    class Config:
        from_attributes = True


class FlightMovementSchema(BaseModel):
    """Flight movement data (departure or arrival)."""

    scheduledTime: Optional[datetime] = Field(None, description="Scheduled time")
    actualTime: Optional[datetime] = Field(None, description="Actual time")
    runwayTime: Optional[datetime] = Field(None, description="Runway time (takeoff/landing)")
    terminal: Optional[str] = Field(None, description="Terminal")
    gate: Optional[str] = Field(None, description="Gate")

    class Config:
        from_attributes = True


class FlightStatusSchema(BaseModel):
    """Flight status response from AeroDataBox API."""

    # Flight identification
    number: str = Field(..., description="Flight number (e.g., 'BA123')")
    callSign: Optional[str] = Field(None, description="ATC call sign")
    iataNumber: Optional[str] = Field(None, description="IATA flight number")
    icaoNumber: Optional[str] = Field(None, description="ICAO flight number")

    # Airline
    airline: Optional[Dict[str, Any]] = Field(None, description="Airline information")

    # Status
    status: Optional[str] = Field(None, description="Flight status (scheduled, delayed, cancelled, etc.)")

    # Movement data
    departure: Optional[FlightMovementSchema] = Field(None, description="Departure information")
    arrival: Optional[FlightMovementSchema] = Field(None, description="Arrival information")

    # Aircraft
    aircraft: Optional[Dict[str, Any]] = Field(None, description="Aircraft information")

    class Config:
        from_attributes = True


class FlightDataResponseSchema(BaseModel):
    """Response schema for flight data stored in database."""

    id: UUID = Field(..., description="Flight data record ID")
    claim_id: UUID = Field(..., description="Associated claim ID")

    # Flight identification
    flight_number: str = Field(..., description="Flight number")
    flight_date: date = Field(..., description="Flight date")
    airline_iata: Optional[str] = Field(None, description="Airline IATA code")
    airline_name: Optional[str] = Field(None, description="Airline name")

    # Airports
    departure_airport_iata: str = Field(..., description="Departure airport IATA code")
    departure_airport_name: Optional[str] = Field(None, description="Departure airport name")
    arrival_airport_iata: str = Field(..., description="Arrival airport IATA code")
    arrival_airport_name: Optional[str] = Field(None, description="Arrival airport name")
    distance_km: Optional[Decimal] = Field(None, description="Flight distance in kilometers")

    # Scheduled times
    scheduled_departure: Optional[datetime] = Field(None, description="Scheduled departure time")
    scheduled_arrival: Optional[datetime] = Field(None, description="Scheduled arrival time")

    # Actual times
    actual_departure: Optional[datetime] = Field(None, description="Actual departure time")
    actual_arrival: Optional[datetime] = Field(None, description="Actual arrival time")

    # Status
    flight_status: Optional[str] = Field(None, description="Flight status")
    delay_minutes: Optional[int] = Field(None, description="Delay in minutes")
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason if applicable")

    # API metadata
    api_source: str = Field(..., description="API source (aerodatabox)")
    api_retrieved_at: datetime = Field(..., description="When data was retrieved from API")

    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")

    class Config:
        from_attributes = True


class EnrichedClaimDataSchema(BaseModel):
    """Enriched claim data with flight verification results."""

    # Flight verification status
    verified: bool = Field(..., description="Whether flight was verified via API")
    verification_source: str = Field(..., description="Verification source (aerodatabox, manual, cached)")

    # Flight data
    flight_number: str = Field(..., description="Flight number")
    flight_date: date = Field(..., description="Flight date")
    airline_name: Optional[str] = Field(None, description="Airline name")

    # Airports and distance
    departure_airport: str = Field(..., description="Departure airport IATA")
    arrival_airport: str = Field(..., description="Arrival airport IATA")
    distance_km: Optional[float] = Field(None, description="Flight distance in km")

    # Delay information
    delay_minutes: Optional[int] = Field(None, description="Delay in minutes")
    delay_hours: Optional[float] = Field(None, description="Delay in hours")
    flight_status: Optional[str] = Field(None, description="Flight status")

    # Compensation calculation
    compensation_amount: Optional[Decimal] = Field(None, description="Calculated compensation in EUR")
    compensation_tier: Optional[str] = Field(None, description="Compensation tier (short/medium/long haul)")
    eligible: Optional[bool] = Field(None, description="Whether claim is eligible for compensation")

    # API usage
    api_credits_used: Optional[int] = Field(None, description="Credits consumed for this verification")
    cached: bool = Field(False, description="Whether data was served from cache")

    class Config:
        from_attributes = True


class APIUsageStatsSchema(BaseModel):
    """API usage statistics response."""

    period_days: int = Field(..., description="Statistics period in days")
    total_calls: int = Field(..., description="Total API calls")
    total_credits: int = Field(..., description="Total credits used")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    max_response_time_ms: int = Field(..., description="Maximum response time in milliseconds")
    daily_usage: list[Dict[str, Any]] = Field(..., description="Daily usage breakdown")
    top_endpoints: list[Dict[str, Any]] = Field(..., description="Top endpoints by usage")

    class Config:
        from_attributes = True


class QuotaStatusSchema(BaseModel):
    """API quota status response."""

    api_provider: str = Field(..., description="API provider name")
    period_start: datetime = Field(..., description="Billing period start")
    period_end: datetime = Field(..., description="Billing period end")

    total_credits_allowed: int = Field(..., description="Total credits allowed in period")
    credits_used: int = Field(..., description="Credits used so far")
    credits_remaining: int = Field(..., description="Credits remaining")
    usage_percentage: float = Field(..., description="Usage percentage")

    is_quota_exceeded: bool = Field(..., description="Whether quota is exceeded (>95%)")

    alerts: Dict[str, Any] = Field(..., description="Alert status (80%, 90%, 95%)")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class FlightVerificationRequestSchema(BaseModel):
    """Request schema for manual flight verification."""

    flight_number: str = Field(..., min_length=3, max_length=10, description="Flight number (e.g., 'BA123')")
    flight_date: str = Field(..., description="Flight date in YYYY-MM-DD format")
    force_refresh: bool = Field(False, description="Force API call even if cached")

    @field_validator('flight_number')
    @classmethod
    def validate_flight_number(cls, v: str) -> str:
        """Validate and normalize flight number."""
        # Uppercase and remove spaces
        v = v.upper().replace(" ", "")

        # Must contain digits
        if not any(char.isdigit() for char in v):
            raise ValueError("Flight number must contain digits")

        return v

    @field_validator('flight_date')
    @classmethod
    def validate_flight_date(cls, v: str) -> str:
        """Validate flight date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Flight date must be in YYYY-MM-DD format")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "flight_number": "BA123",
                "flight_date": "2024-01-15",
                "force_refresh": False
            }
        }


# ============================================================================
# Phase 6.5: Flight Search by Route Schemas
# ============================================================================


class AirportSearchResultSchema(BaseModel):
    """Airport autocomplete result schema."""

    iata: str = Field(..., min_length=3, max_length=3, description="IATA airport code")
    icao: Optional[str] = Field(None, min_length=4, max_length=4, description="ICAO airport code")
    name: str = Field(..., description="Airport name")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name or code")

    @field_validator('iata')
    @classmethod
    def validate_iata(cls, v: str) -> str:
        """Validate and normalize IATA code."""
        return v.upper()

    @field_validator('icao')
    @classmethod
    def validate_icao(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize ICAO code."""
        return v.upper() if v else None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "iata": "MUC",
                "icao": "EDDM",
                "name": "Munich Airport",
                "city": "Munich",
                "country": "Germany"
            }
        }


class FlightSearchResultSchema(BaseModel):
    """Flight search result schema (route search)."""

    flightNumber: str = Field(..., description="Flight number")
    airline: Optional[str] = Field(None, description="Airline name")
    airlineIata: Optional[str] = Field(None, description="Airline IATA code")

    departureAirport: str = Field(..., description="Departure airport IATA code")
    departureAirportName: Optional[str] = Field(None, description="Departure airport name")
    arrivalAirport: str = Field(..., description="Arrival airport IATA code")
    arrivalAirportName: Optional[str] = Field(None, description="Arrival airport name")

    scheduledDeparture: Optional[str] = Field(None, description="Scheduled departure time (ISO 8601)")
    scheduledArrival: Optional[str] = Field(None, description="Scheduled arrival time (ISO 8601)")
    actualDeparture: Optional[str] = Field(None, description="Actual departure time (ISO 8601)")
    actualArrival: Optional[str] = Field(None, description="Actual arrival time (ISO 8601)")

    status: str = Field(..., description="Flight status (scheduled, delayed, cancelled, etc.)")
    delayMinutes: Optional[int] = Field(None, description="Delay in minutes")
    distanceKm: Optional[float] = Field(None, description="Flight distance in kilometers")

    estimatedCompensation: Optional[int] = Field(None, description="Estimated EU261 compensation in EUR")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "flightNumber": "LH8960",
                "airline": "Lufthansa",
                "airlineIata": "LH",
                "departureAirport": "MUC",
                "departureAirportName": "Munich Airport",
                "arrivalAirport": "JFK",
                "arrivalAirportName": "John F. Kennedy International",
                "scheduledDeparture": "2025-01-15T13:45:00+01:00",
                "scheduledArrival": "2025-01-15T17:20:00-05:00",
                "actualDeparture": "2025-01-15T16:45:00+01:00",
                "actualArrival": "2025-01-15T20:20:00-05:00",
                "status": "delayed",
                "delayMinutes": 180,
                "distanceKm": 6200.0,
                "estimatedCompensation": 600
            }
        }


class RouteSearchRequestSchema(BaseModel):
    """Request schema for route search."""

    departure_iata: str = Field(..., min_length=3, max_length=3, description="Departure airport IATA code")
    arrival_iata: str = Field(..., min_length=3, max_length=3, description="Arrival airport IATA code")
    flight_date: str = Field(..., description="Flight date in YYYY-MM-DD format")
    approximate_time: Optional[str] = Field(None, description="Approximate time (morning/afternoon/evening or HH:MM)")

    @field_validator('departure_iata', 'arrival_iata')
    @classmethod
    def validate_iata_codes(cls, v: str) -> str:
        """Validate and normalize IATA codes."""
        v = v.upper().strip()
        if len(v) != 3 or not v.isalpha():
            raise ValueError("IATA code must be exactly 3 letters")
        return v

    @field_validator('flight_date')
    @classmethod
    def validate_flight_date(cls, v: str) -> str:
        """Validate flight date format and range."""
        try:
            flight_date = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Flight date must be in YYYY-MM-DD format")

        # Check date is not in the future
        today = datetime.now().date()
        if flight_date > today:
            raise ValueError("Flight date cannot be in the future")

        # Check date is not more than 6 years ago (EU261 claim window varies by jurisdiction)
        # UK: 6 years, Germany: 3 years, most EU countries: 2-3 years
        # We use 6 years to be inclusive
        six_years_ago = today - timedelta(days=365 * 6)
        if flight_date < six_years_ago:
            raise ValueError("Flight date must be within the last 6 years")

        return v

    @field_validator('approximate_time')
    @classmethod
    def validate_approximate_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate approximate time format."""
        if v is None or v == "":
            return None

        v = v.lower().strip()

        # Check if it's one of the predefined options
        valid_options = ['morning', 'afternoon', 'evening']
        if v in valid_options:
            return v

        # Check if it's HH:MM format
        if ':' in v:
            try:
                time_parts = v.split(':')
                if len(time_parts) != 2:
                    raise ValueError()
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError()
                return v
            except (ValueError, IndexError):
                raise ValueError("Time must be in HH:MM format (e.g., '14:30')")

        raise ValueError("Approximate time must be 'morning', 'afternoon', 'evening', or 'HH:MM' format")

    class Config:
        json_schema_extra = {
            "example": {
                "departure_iata": "MUC",
                "arrival_iata": "JFK",
                "flight_date": "2025-01-15",
                "approximate_time": "afternoon"
            }
        }


class AirportSearchRequestSchema(BaseModel):
    """Request schema for airport search."""

    query: str = Field(..., min_length=2, max_length=50, description="Search query (IATA code, city, or airport name)")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results to return")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and normalize search query."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "munich",
                "limit": 10
            }
        }


class RouteSearchResponseSchema(BaseModel):
    """Response schema for route search."""

    flights: list[FlightSearchResultSchema] = Field(..., description="List of matching flights")
    total: int = Field(..., description="Total number of flights found")
    cached: bool = Field(False, description="Whether results were served from cache")
    apiCreditsUsed: int = Field(0, description="Number of API credits consumed")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "flights": [
                    {
                        "flightNumber": "LH8960",
                        "airline": "Lufthansa",
                        "airlineIata": "LH",
                        "departureAirport": "MUC",
                        "arrivalAirport": "JFK",
                        "scheduledDeparture": "2025-01-15T13:45:00+01:00",
                        "scheduledArrival": "2025-01-15T17:20:00-05:00",
                        "status": "delayed",
                        "delayMinutes": 180,
                        "estimatedCompensation": 600
                    }
                ],
                "total": 1,
                "cached": False,
                "apiCreditsUsed": 2
            }
        }


class AirportSearchResponseSchema(BaseModel):
    """Response schema for airport search."""

    airports: list[AirportSearchResultSchema] = Field(..., description="List of matching airports")
    total: int = Field(..., description="Total number of airports found")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "airports": [
                    {
                        "iata": "MUC",
                        "icao": "EDDM",
                        "name": "Munich Airport",
                        "city": "Munich",
                        "country": "Germany"
                    }
                ],
                "total": 1
            }
        }
