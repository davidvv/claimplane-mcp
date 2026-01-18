"""Pydantic schemas for OCR boarding pass extraction."""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class FlightSegmentSchema(BaseModel):
    """Schema for a single flight segment."""
    flight_number: Optional[str] = Field(None, alias="flightNumber")
    departure_airport: Optional[str] = Field(None, alias="departureAirport")
    arrival_airport: Optional[str] = Field(None, alias="arrivalAirport")
    departure_date: Optional[str] = Field(None, alias="departureDate")
    departure_time: Optional[str] = Field(None, alias="departureTime")
    arrival_time: Optional[str] = Field(None, alias="arrivalTime")
    airline: Optional[str] = None
    # Leg type: "outbound", "outbound_connection", "return", "return_connection"
    leg_type: Optional[str] = Field(None, alias="legType")
    # Trip index: groups flights into logical trips (1=outbound journey, 2=return journey, etc.)
    trip_index: Optional[int] = Field(None, alias="tripIndex")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class PassengerSchema(BaseModel):
    """Schema for a single passenger."""
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    ticket_number: Optional[str] = Field(None, alias="ticketNumber")
    booking_reference: Optional[str] = Field(None, alias="bookingReference")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class BoardingPassDataSchema(BaseModel):
    """Extracted flight data from boarding pass OCR."""

    flight_number: Optional[str] = Field(None, alias="flightNumber")
    departure_airport: Optional[str] = Field(None, alias="departureAirport")
    arrival_airport: Optional[str] = Field(None, alias="arrivalAirport")
    flight_date: Optional[str] = Field(None, alias="flightDate")
    departure_time: Optional[str] = Field(None, alias="departureTime")
    arrival_time: Optional[str] = Field(None, alias="arrivalTime")
    passenger_name: Optional[str] = Field(None, alias="passengerName")
    booking_reference: Optional[str] = Field(None, alias="bookingReference")
    seat_number: Optional[str] = Field(None, alias="seatNumber")
    airline: Optional[str] = None
    incident_type: Optional[str] = Field(None, alias="incidentType")
    delay_minutes: Optional[int] = Field(None, alias="delayMinutes")
    cancellation_reason: Optional[str] = Field(None, alias="cancellationReason")

    # New fields for multi-passenger/multi-segment
    passengers: Optional[List[PassengerSchema]] = None
    flights: Optional[List[FlightSegmentSchema]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class FieldConfidenceSchema(BaseModel):
    """Confidence scores for individual extracted fields."""

    flight_number: Optional[float] = Field(None, alias="flightNumber", ge=0.0, le=1.0)
    departure_airport: Optional[float] = Field(None, alias="departureAirport", ge=0.0, le=1.0)
    arrival_airport: Optional[float] = Field(None, alias="arrivalAirport", ge=0.0, le=1.0)
    flight_date: Optional[float] = Field(None, alias="flightDate", ge=0.0, le=1.0)
    departure_time: Optional[float] = Field(None, alias="departureTime", ge=0.0, le=1.0)
    passenger_name: Optional[float] = Field(None, alias="passengerName", ge=0.0, le=1.0)
    booking_reference: Optional[float] = Field(None, alias="bookingReference", ge=0.0, le=1.0)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class OCRResponseSchema(BaseModel):
    """Response schema for OCR boarding pass extraction endpoint."""

    success: bool
    data: Optional[BoardingPassDataSchema] = None
    raw_text: str = Field("", alias="rawText")
    confidence_score: float = Field(0.0, alias="confidenceScore", ge=0.0, le=1.0)
    field_confidence: Optional[FieldConfidenceSchema] = Field(None, alias="fieldConfidence")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None, alias="processingTimeMs")
    uploaded_file_id: Optional[str] = Field(None, alias="uploadedFileId")  # ID of saved file for later linking

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )
