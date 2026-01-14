"""Tests for OCR boarding pass extraction service."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.ocr_service import OCRService


class TestOCRPatternMatching:
    """Test regex pattern matching for boarding pass data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_find_flight_number_standard(self):
        """Test extracting standard flight numbers."""
        assert self.service._find_flight_number("FLIGHT LH123 MUNICH") == "LH123"
        assert self.service._find_flight_number("BA456 LONDON HEATHROW") == "BA456"
        assert self.service._find_flight_number("FR1234") == "FR1234"

    def test_find_flight_number_with_space(self):
        """Test extracting flight numbers with space."""
        assert self.service._find_flight_number("LH 123") == "LH123"

    def test_find_flight_number_numeric_airline(self):
        """Test extracting flight numbers with numeric airline codes."""
        assert self.service._find_flight_number("U2 456") == "U2456"

    def test_find_flight_number_none(self):
        """Test when no flight number found."""
        assert self.service._find_flight_number("NO FLIGHT HERE") is None

    def test_find_date_dmy_format(self):
        """Test extracting dates in DD/MM/YYYY format."""
        assert self.service._find_date("DATE 15/01/2024") == "2024-01-15"
        assert self.service._find_date("15.01.2024") == "2024-01-15"
        assert self.service._find_date("15-01-24") == "2024-01-15"

    def test_find_date_iso_format(self):
        """Test extracting dates in YYYY-MM-DD format."""
        assert self.service._find_date("2024-01-15") == "2024-01-15"
        assert self.service._find_date("DATE: 2024/01/15") == "2024-01-15"

    def test_find_date_none(self):
        """Test when no date found."""
        assert self.service._find_date("NO DATE HERE") is None

    def test_find_passenger_name(self):
        """Test extracting passenger name in LASTNAME/FIRSTNAME format."""
        assert self.service._find_passenger_name("SMITH/JOHN MR") == "SMITH/JOHN"
        assert self.service._find_passenger_name("DOE/JANE") == "DOE/JANE"

    def test_find_passenger_name_none(self):
        """Test when no passenger name found."""
        assert self.service._find_passenger_name("NO NAME HERE") is None

    def test_find_seat(self):
        """Test extracting seat numbers."""
        assert self.service._find_seat("SEAT 12A") == "12A"
        assert self.service._find_seat("SEAT: 1F") == "1F"

    def test_find_seat_without_context(self):
        """Test seat not found without context keyword."""
        assert self.service._find_seat("ROW 12A WINDOW") is None


class TestAirportCodeExtraction:
    """Test airport code extraction logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_find_airport_codes_with_context(self):
        """Test extracting airports with FROM/TO context."""
        text = "FROM FRA TO JFK\nFLIGHT LH123"
        lines = text.split('\n')
        result = self.service._find_airport_codes(text, lines)
        assert result.get("departure") == "FRA"
        assert result.get("arrival") == "JFK"

    def test_find_airport_codes_departure_keyword(self):
        """Test extracting airports with DEPARTURE keyword."""
        text = "DEPARTURE LHR\nARRIVAL CDG"
        lines = text.split('\n')
        result = self.service._find_airport_codes(text, lines)
        assert result.get("departure") == "LHR"
        assert result.get("arrival") == "CDG"

    def test_find_airport_codes_positional(self):
        """Test fallback to positional extraction."""
        text = "FRA JFK LH123"
        lines = text.split('\n')
        result = self.service._find_airport_codes(text, lines)
        assert result.get("departure") == "FRA"
        assert result.get("arrival") == "JFK"

    def test_filter_common_words(self):
        """Test that common 3-letter words are filtered out."""
        text = "THE AND FOR ARE FRA JFK"
        lines = text.split('\n')
        result = self.service._find_airport_codes(text, lines)
        # Should only get FRA and JFK, not THE, AND, FOR, ARE
        assert result.get("departure") == "FRA"
        assert result.get("arrival") == "JFK"


class TestTimeExtraction:
    """Test time extraction logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_find_times_with_context(self):
        """Test extracting times with DEP/ARR context."""
        text = "DEP 10:30\nARR 14:45"
        lines = text.split('\n')
        result = self.service._find_times(text, lines)
        assert result.get("departure") == "10:30"
        assert result.get("arrival") == "14:45"

    def test_find_times_positional(self):
        """Test fallback to positional extraction."""
        text = "FLIGHT LH123 08:00 12:30"
        lines = text.split('\n')
        result = self.service._find_times(text, lines)
        assert result.get("departure") == "08:00"
        assert result.get("arrival") == "12:30"

    def test_filter_invalid_times(self):
        """Test that invalid times (>23:59) are filtered."""
        text = "25:00 10:30"
        lines = text.split('\n')
        result = self.service._find_times(text, lines)
        assert result.get("departure") == "10:30"


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_overall_confidence_full(self):
        """Test confidence calculation with all fields."""
        field_confidence = {
            "flight_number": 0.9,
            "departure_airport": 0.8,
            "arrival_airport": 0.8,
            "flight_date": 0.7,
            "departure_time": 0.6,
        }
        score = self.service._calculate_overall_confidence(field_confidence)
        assert 0.7 < score < 0.9

    def test_overall_confidence_partial(self):
        """Test confidence calculation with partial fields."""
        field_confidence = {
            "flight_number": 0.9,
        }
        score = self.service._calculate_overall_confidence(field_confidence)
        assert score == 0.9

    def test_overall_confidence_empty(self):
        """Test confidence calculation with no fields."""
        score = self.service._calculate_overall_confidence({})
        assert score == 0.0


class TestTextParsing:
    """Test full text parsing pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_parse_sample_boarding_pass(self):
        """Test parsing a sample boarding pass text."""
        sample_text = """
        LUFTHANSA
        BOARDING PASS

        SMITH/JOHN MR

        FROM: FRA  TO: JFK
        FLIGHT: LH456
        DATE: 15/01/2024

        DEP: 10:30  ARR: 14:45
        SEAT: 12A

        BOOKING REF: ABC123
        """

        data, confidence = self.service._parse_boarding_pass_text(sample_text)

        assert data["flight_number"] == "LH456"
        assert data["departure_airport"] == "FRA"
        assert data["arrival_airport"] == "JFK"
        assert data["flight_date"] == "2024-01-15"
        assert data["passenger_name"] == "SMITH/JOHN"
        assert data["seat_number"] == "12A"

        # Check confidence scores exist
        assert "flight_number" in confidence
        assert confidence["flight_number"] > 0


class TestDependencyCheck:
    """Test dependency checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_check_dependencies(self):
        """Test dependency check returns expected keys."""
        deps = self.service._check_dependencies()
        assert "tesseract" in deps
        assert "opencv" in deps
        assert "pdf" in deps


@pytest.mark.asyncio
class TestOCRExtraction:
    """Test full OCR extraction pipeline."""

    async def test_extract_empty_file(self):
        """Test handling of empty file content."""
        service = OCRService()

        # Mock dependencies check to return tesseract available
        with patch.object(service, '_check_dependencies', return_value={"tesseract": True, "opencv": True, "pdf": False}):
            with patch.object(service, '_load_image', return_value=None):
                result = await service.extract_boarding_pass_data(
                    file_content=b"",
                    mime_type="image/jpeg"
                )

                assert result["success"] is False
                assert len(result["errors"]) > 0

    async def test_extract_no_tesseract(self):
        """Test handling when tesseract is not available."""
        service = OCRService()

        with patch.object(service, '_check_dependencies', return_value={"tesseract": False, "opencv": False, "pdf": False}):
            result = await service.extract_boarding_pass_data(
                file_content=b"test content",
                mime_type="image/jpeg"
            )

            assert result["success"] is False
            assert "Tesseract OCR is not installed" in result["errors"][0]

    async def test_extract_with_mock_ocr(self):
        """Test extraction with mocked OCR output."""
        service = OCRService()

        mock_image = MagicMock()
        mock_text = """
        BRITISH AIRWAYS
        BOARDING PASS
        SMITH/JOHN
        FROM LHR TO JFK
        BA178
        DATE 20/01/2024
        DEP 08:30
        """

        with patch.object(service, '_check_dependencies', return_value={"tesseract": True, "opencv": True, "pdf": False}):
            with patch.object(service, '_load_image', return_value=mock_image):
                with patch.object(service, '_preprocess_image', return_value=mock_image):
                    with patch.object(service, '_run_ocr', return_value=mock_text):
                        result = await service.extract_boarding_pass_data(
                            file_content=b"test content",
                            mime_type="image/jpeg"
                        )

                        assert result["success"] is True
                        assert result["data"]["flight_number"] == "BA178"
                        assert result["data"]["departure_airport"] == "LHR"
                        assert result["data"]["arrival_airport"] == "JFK"
                        assert result["confidence_score"] > 0


class TestValidation:
    """Test data validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = OCRService()

    def test_validate_missing_fields(self):
        """Test validation warnings for missing fields."""
        data = {
            "flight_number": None,
            "departure_airport": None,
            "arrival_airport": None,
            "flight_date": None,
        }

        errors, warnings = self.service._validate_extracted_data(data)

        assert len(warnings) > 0
        assert any("flight number" in w.lower() for w in warnings)
        assert any("airport" in w.lower() for w in warnings)
        assert any("date" in w.lower() for w in warnings)

    def test_validate_complete_data(self):
        """Test validation with complete data."""
        data = {
            "flight_number": "LH123",
            "departure_airport": "FRA",
            "arrival_airport": "JFK",
            "flight_date": "2024-01-15",
        }

        # Mock airport validation
        with patch.object(self.service, '_is_valid_airport', return_value=True):
            errors, warnings = self.service._validate_extracted_data(data)

            # Should have no errors for required fields
            assert not any("flight number" in w.lower() for w in warnings)
