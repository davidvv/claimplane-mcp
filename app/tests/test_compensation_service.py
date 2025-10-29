"""Tests for compensation calculation service."""
import pytest
from decimal import Decimal

from app.services.compensation_service import CompensationService


class TestDistanceCalculation:
    """Test distance calculation between airports."""

    def test_short_haul_distance(self):
        """Test calculation for short haul flight."""
        # London to Paris - approximately 350 km
        distance = CompensationService.calculate_distance("LHR", "CDG")
        assert distance is not None
        assert 300 < distance < 400

    def test_medium_haul_distance(self):
        """Test calculation for medium haul flight."""
        # London to Istanbul - approximately 2500 km
        distance = CompensationService.calculate_distance("LHR", "IST")
        assert distance is not None
        assert 2400 < distance < 2600

    def test_long_haul_distance(self):
        """Test calculation for long haul flight."""
        # London to New York - approximately 5500 km
        distance = CompensationService.calculate_distance("LHR", "JFK")
        assert distance is not None
        assert 5400 < distance < 5600

    def test_unknown_airport(self):
        """Test handling of unknown airport codes."""
        distance = CompensationService.calculate_distance("XXX", "YYY")
        assert distance is None

    def test_case_insensitive(self):
        """Test that airport codes are case insensitive."""
        distance1 = CompensationService.calculate_distance("lhr", "cdg")
        distance2 = CompensationService.calculate_distance("LHR", "CDG")
        assert distance1 == distance2


class TestBaseCompensation:
    """Test base compensation calculation by distance."""

    def test_short_haul_compensation(self):
        """Test compensation for flights < 1500 km."""
        compensation = CompensationService.get_base_compensation(1000)
        assert compensation == Decimal("250")

    def test_medium_haul_compensation(self):
        """Test compensation for flights 1500-3500 km."""
        compensation = CompensationService.get_base_compensation(2000)
        assert compensation == Decimal("400")

    def test_long_haul_compensation(self):
        """Test compensation for flights > 3500 km."""
        compensation = CompensationService.get_base_compensation(5000)
        assert compensation == Decimal("600")

    def test_boundary_short_medium(self):
        """Test boundary between short and medium haul."""
        # Just below threshold
        comp1 = CompensationService.get_base_compensation(1499)
        assert comp1 == Decimal("250")

        # At threshold
        comp2 = CompensationService.get_base_compensation(1500)
        assert comp2 == Decimal("400")

    def test_boundary_medium_long(self):
        """Test boundary between medium and long haul."""
        # Just below threshold
        comp1 = CompensationService.get_base_compensation(3499)
        assert comp1 == Decimal("400")

        # At threshold
        comp2 = CompensationService.get_base_compensation(3500)
        assert comp2 == Decimal("600")


class TestExtraordinaryCircumstances:
    """Test extraordinary circumstances detection."""

    def test_weather_detection(self):
        """Test detection of weather-related circumstances."""
        is_extraordinary, keyword = CompensationService.check_extraordinary_circumstances(
            incident_description="Flight cancelled due to severe weather conditions"
        )
        assert is_extraordinary is True
        assert keyword == "weather"

    def test_strike_detection(self):
        """Test detection of strike-related circumstances."""
        is_extraordinary, keyword = CompensationService.check_extraordinary_circumstances(
            cancellation_reason="Airport strike"
        )
        assert is_extraordinary is True
        assert keyword == "strike"

    def test_no_extraordinary_circumstances(self):
        """Test when no extraordinary circumstances are present."""
        is_extraordinary, keyword = CompensationService.check_extraordinary_circumstances(
            incident_description="Technical issue with aircraft"
        )
        assert is_extraordinary is False
        assert keyword is None

    def test_empty_description(self):
        """Test handling of empty descriptions."""
        is_extraordinary, keyword = CompensationService.check_extraordinary_circumstances()
        assert is_extraordinary is False
        assert keyword is None


class TestDelayCompensation:
    """Test compensation calculation for delays."""

    def test_short_haul_delay_eligible(self):
        """Test short haul flight with 3+ hour delay."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            delay_hours=4.0,
            incident_type="delay"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("250")
        assert "3" in result["reason"].lower() or "4" in result["reason"]

    def test_short_haul_delay_not_eligible(self):
        """Test short haul flight with < 3 hour delay."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            delay_hours=2.5,
            incident_type="delay"
        )

        assert result["eligible"] is False
        assert result["amount"] == Decimal("0")
        assert "less than minimum" in result["reason"].lower()

    def test_long_haul_partial_compensation(self):
        """Test long haul flight with 3-4 hour delay gets 50% compensation."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="JFK",
            delay_hours=3.5,
            incident_type="delay"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("300")  # 50% of 600
        assert "50%" in result["reason"]

    def test_long_haul_full_compensation(self):
        """Test long haul flight with 4+ hour delay gets full compensation."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="JFK",
            delay_hours=5.0,
            incident_type="delay"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("600")

    def test_delay_without_hours(self):
        """Test delay incident without specifying hours."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="delay"
        )

        assert result["requires_manual_review"] is True
        assert "not specified" in result["reason"].lower()


class TestCancellationCompensation:
    """Test compensation calculation for cancellations."""

    def test_short_haul_cancellation(self):
        """Test cancellation on short haul flight."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="cancellation"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("250")

    def test_medium_haul_cancellation(self):
        """Test cancellation on medium haul flight."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="IST",
            incident_type="cancellation"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("400")

    def test_cancellation_with_alternative(self):
        """Test cancellation with alternative flight offered."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="cancellation",
            alternative_flight_offered=True
        )

        assert result["eligible"] is True
        assert result["requires_manual_review"] is True
        assert "alternative" in result["reason"].lower()


class TestDeniedBoarding:
    """Test compensation calculation for denied boarding."""

    def test_denied_boarding_short_haul(self):
        """Test denied boarding on short haul flight."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="denied_boarding"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("250")

    def test_denied_boarding_long_haul(self):
        """Test denied boarding on long haul flight."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="JFK",
            incident_type="denied_boarding"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("600")


class TestBaggageDelay:
    """Test compensation calculation for baggage delay."""

    def test_baggage_delay_not_covered(self):
        """Test that baggage delay is not covered by EU261."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="baggage_delay"
        )

        assert result["eligible"] is False
        assert result["amount"] == Decimal("0")
        assert "montreal convention" in result["reason"].lower()
        assert result["requires_manual_review"] is True


class TestExtraordinaryCircumstancesCompensation:
    """Test compensation with extraordinary circumstances."""

    def test_weather_cancellation_no_compensation(self):
        """Test that weather-related cancellations get no compensation."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="cancellation",
            extraordinary_circumstances="Severe storm"
        )

        assert result["eligible"] is False
        assert result["amount"] == Decimal("0")
        assert "extraordinary" in result["reason"].lower()
        assert result["requires_manual_review"] is True

    def test_strike_delay_no_compensation(self):
        """Test that strike-related delays get no compensation."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            delay_hours=5.0,
            incident_type="delay",
            extraordinary_circumstances="Air traffic control strike"
        )

        assert result["eligible"] is False
        assert result["amount"] == Decimal("0")


class TestSimpleEstimate:
    """Test simple compensation estimation."""

    def test_simple_estimate_short_haul(self):
        """Test simple estimate for short haul."""
        estimate = CompensationService.estimate_compensation_simple(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="delay"
        )

        assert estimate == Decimal("250")

    def test_simple_estimate_long_haul(self):
        """Test simple estimate for long haul."""
        estimate = CompensationService.estimate_compensation_simple(
            departure_airport="LHR",
            arrival_airport="JFK",
            incident_type="delay"
        )

        assert estimate == Decimal("600")

    def test_simple_estimate_baggage(self):
        """Test simple estimate for baggage delay."""
        estimate = CompensationService.estimate_compensation_simple(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="baggage_delay"
        )

        assert estimate == Decimal("0")

    def test_simple_estimate_unknown_airport(self):
        """Test simple estimate with unknown airport."""
        estimate = CompensationService.estimate_compensation_simple(
            departure_airport="XXX",
            arrival_airport="YYY",
            incident_type="delay"
        )

        assert estimate == Decimal("0")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_exact_3_hour_delay(self):
        """Test that exactly 3 hours delay qualifies."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            delay_hours=3.0,
            incident_type="delay"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("250")

    def test_exact_4_hour_delay_long_haul(self):
        """Test that exactly 4 hours delay on long haul gets full compensation."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="JFK",
            delay_hours=4.0,
            incident_type="delay"
        )

        assert result["eligible"] is True
        assert result["amount"] == Decimal("600")  # Full compensation, not 50%

    def test_unknown_incident_type(self):
        """Test handling of unknown incident type."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            incident_type="unknown_type"
        )

        assert result["requires_manual_review"] is True
        assert "unknown incident type" in result["reason"].lower()

    def test_pre_calculated_distance(self):
        """Test using pre-calculated distance."""
        result = CompensationService.calculate_compensation(
            departure_airport="LHR",
            arrival_airport="CDG",
            delay_hours=4.0,
            incident_type="delay",
            distance_km=350.0
        )

        assert result["eligible"] is True
        assert result["distance_km"] == 350.0
        assert result["amount"] == Decimal("250")
