"""
OCR Service for extracting flight data from boarding pass images.

Uses Tesseract OCR with image preprocessing to extract flight details
from boarding pass images (JPEG, PNG, PDF).
"""

import io
import logging
import re
import time
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class OCRService:
    """
    Extract flight data from boarding pass images using OCR.

    Supports:
    - JPEG, PNG, WebP images
    - PDF documents (first page)
    - Image preprocessing for better accuracy
    """

    # Regex patterns for extracting boarding pass data
    PATTERNS = {
        # Flight number: 2-letter airline code + 1-4 digits (e.g., LH123, BA1234, U24567)
        "flight_number": r"\b([A-Z]{2}|[A-Z]\d|\d[A-Z])\s*(\d{1,4})\b",
        # IATA airport codes: exactly 3 uppercase letters
        "airport_code": r"\b([A-Z]{3})\b",
        # Date formats: DD/MM/YYYY, DD.MM.YY, DD-MM-YYYY, etc.
        "date_dmy": r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b",
        # Date formats: YYYY-MM-DD (ISO format)
        "date_iso": r"\b(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})\b",
        # Time: HH:MM format
        "time": r"\b(\d{1,2}):(\d{2})\b",
        # Booking reference: 6 alphanumeric characters
        "booking_ref": r"\b([A-Z0-9]{6})\b",
        # Passenger name: LASTNAME/FIRSTNAME format
        "passenger_name": r"\b([A-Z]{2,})\s*/\s*([A-Z]{2,})\b",
        # Seat number: row + letter (e.g., 12A, 1F)
        "seat": r"\b(\d{1,2})([A-Z])\b",
    }

    # Common flight-related keywords to help identify context
    CONTEXT_KEYWORDS = {
        "flight": ["flight", "flug", "vol", "vuelo", "volo"],
        "from": ["from", "departure", "dep", "von", "depart", "origin"],
        "to": ["to", "arrival", "arr", "nach", "dest", "destination"],
        "date": ["date", "datum", "fecha", "data"],
        "time": ["time", "zeit", "hora", "ora", "boarding"],
        "gate": ["gate", "tor", "puerta", "porta"],
        "seat": ["seat", "sitz", "asiento", "posto", "place"],
        "passenger": ["passenger", "passagier", "pasajero", "passeggero", "name"],
        "booking": ["booking", "buchung", "reserva", "prenotazione", "pnr", "confirmation"],
    }

    def __init__(self):
        """Initialize OCR service."""
        self._tesseract_available = None
        self._opencv_available = None
        self._pdf_available = None

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if OCR dependencies are available."""
        status = {}

        # Check pytesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            status["tesseract"] = True
        except Exception:
            status["tesseract"] = False

        # Check OpenCV
        try:
            import cv2
            status["opencv"] = True
        except ImportError:
            status["opencv"] = False

        # Check PDF support
        try:
            from pdf2image import convert_from_bytes
            status["pdf"] = True
        except ImportError:
            status["pdf"] = False

        return status

    async def extract_boarding_pass_data(
        self,
        file_content: bytes,
        mime_type: str,
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract flight details from boarding pass image.

        Args:
            file_content: Raw file bytes
            mime_type: MIME type of file
            preprocessing: Whether to apply image preprocessing

        Returns:
            Dictionary with extracted data, confidence scores, and any errors
        """
        start_time = time.time()
        result = {
            "success": False,
            "data": None,
            "raw_text": "",
            "confidence_score": 0.0,
            "field_confidence": {},
            "errors": [],
            "warnings": [],
            "processing_time_ms": 0,
        }

        try:
            # Check dependencies
            deps = self._check_dependencies()
            if not deps.get("tesseract"):
                result["errors"].append("Tesseract OCR is not installed or not accessible")
                return result

            # Convert file to image
            image = await self._load_image(file_content, mime_type, deps)
            if image is None:
                result["errors"].append(f"Failed to load image from {mime_type} file")
                return result

            # Preprocess image if enabled - creates multiple variants
            if preprocessing and deps.get("opencv"):
                image_variants = self._preprocess_image(image)
            else:
                image_variants = [("original", image)]

            # Try OCR on each variant and keep the best result
            best_raw_text = ""
            best_field_count = 0
            best_data = None
            best_confidence = None

            logger.info(f"Running OCR on {len(image_variants)} image variants...")

            for variant_name, variant_image in image_variants:
                logger.info(f"Processing variant: {variant_name}")

                # Run OCR on this variant
                variant_text = self._run_ocr(variant_image)

                if not variant_text or len(variant_text.strip()) < 10:
                    logger.info(f"Variant {variant_name} extracted insufficient text")
                    continue

                # Parse this variant's text
                variant_data, variant_confidence = self._parse_boarding_pass_text(variant_text)

                # Count how many fields were extracted
                field_count = sum(1 for v in variant_data.values() if v is not None)

                logger.info(f"Variant {variant_name}: {field_count} fields extracted, {len(variant_text)} chars")

                # Keep the variant with most fields extracted
                if field_count > best_field_count:
                    best_raw_text = variant_text
                    best_field_count = field_count
                    best_data = variant_data
                    best_confidence = variant_confidence
                    logger.info(f"New best variant: {variant_name} with {field_count} fields")

            if not best_raw_text or best_field_count == 0:
                result["errors"].append("OCR could not extract boarding pass data from any image variant")
                return result

            logger.info(f"Best result: {best_field_count} fields extracted from {len(best_raw_text)} characters")

            result["raw_text"] = best_raw_text
            extracted_data = best_data
            field_confidence = best_confidence

            # Validate extracted data
            validation_errors, validation_warnings = self._validate_extracted_data(extracted_data)
            result["warnings"].extend(validation_warnings)

            if validation_errors:
                result["warnings"].extend(validation_errors)

            # Calculate overall confidence score
            overall_confidence = self._calculate_overall_confidence(field_confidence)

            # Build result
            result["success"] = True
            result["data"] = extracted_data
            result["field_confidence"] = field_confidence
            result["confidence_score"] = overall_confidence

            # Add warning if confidence is low
            if overall_confidence < 0.5:
                result["warnings"].append(
                    "Low confidence extraction - please verify all fields manually"
                )
            elif overall_confidence < 0.7:
                result["warnings"].append(
                    "Some fields may need verification"
                )

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            result["errors"].append(f"OCR processing error: {str(e)}")

        finally:
            result["processing_time_ms"] = int((time.time() - start_time) * 1000)

        return result

    async def _load_image(
        self,
        file_content: bytes,
        mime_type: str,
        deps: Dict[str, bool]
    ) -> Optional[Any]:
        """Load image from file content based on MIME type."""
        try:
            from PIL import Image

            if mime_type in ["image/jpeg", "image/png", "image/webp"]:
                return Image.open(io.BytesIO(file_content))

            elif mime_type == "application/pdf":
                if not deps.get("pdf"):
                    logger.warning("pdf2image not available, PDF support disabled")
                    return None

                from pdf2image import convert_from_bytes
                # Convert first page of PDF to image
                images = convert_from_bytes(file_content, first_page=1, last_page=1)
                if images:
                    return images[0]
                return None

            else:
                logger.warning(f"Unsupported MIME type: {mime_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to load image: {str(e)}", exc_info=True)
            return None

    def _is_clean_digital_image(self, image: Any) -> bool:
        """
        Detect if image is a clean digital screenshot (vs blurry photo).
        Clean screenshots don't need preprocessing.
        """
        try:
            import cv2
            import numpy as np

            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Check sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Check contrast
            contrast = gray.std()

            # If sharp (>100) and good contrast (>50), it's likely a clean digital image
            # Digital screenshots: laplacian_var > 500, contrast > 60
            # Blurry photos: laplacian_var < 100, contrast < 50
            is_clean = laplacian_var > 200 and contrast > 40

            logger.info(f"Image quality check: laplacian_var={laplacian_var:.1f}, contrast={contrast:.1f}, is_clean={is_clean}")
            return is_clean

        except Exception as e:
            logger.warning(f"Image quality check failed: {str(e)}")
            return False

    def _preprocess_image(self, image: Any) -> list:
        """
        Preprocess image for better OCR results.
        Returns multiple preprocessed versions to try OCR on each.
        """
        try:
            import cv2
            import numpy as np
            from PIL import Image

            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            is_clean = self._is_clean_digital_image(image)
            variants = []

            # Variant 1: Original grayscale
            variants.append(("original_gray", Image.fromarray(gray)))

            # Variant 2: Upscaled 3x for better text recognition (slow but accurate)
            height, width = gray.shape
            upscaled_3x = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
            variants.append(("upscaled_3x", Image.fromarray(upscaled_3x)))

            if not is_clean:
                logger.info("Blurry/photo image - creating enhanced variants")

                # Variant 3: CLAHE enhanced
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                variants.append(("clahe", Image.fromarray(enhanced)))

                # Variant 4: Denoised
                denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
                variants.append(("denoised", Image.fromarray(denoised)))

                # Variant 5: Binary threshold
                binary = cv2.adaptiveThreshold(
                    denoised,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )
                variants.append(("binary", Image.fromarray(binary)))

                # Variant 6: Otsu thresholding
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                variants.append(("otsu", Image.fromarray(otsu)))
            else:
                logger.info("Clean digital image - using minimal preprocessing")

                # Variant 3: Slight sharpening for digital images
                kernel_sharpen = np.array([[-1,-1,-1],
                                          [-1, 9,-1],
                                          [-1,-1,-1]])
                sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
                variants.append(("sharpened", Image.fromarray(sharpened)))

                # Variant 4: Upscaled 4x (aggressive but good for small text)
                upscaled_4x = cv2.resize(gray, (width * 4, height * 4), interpolation=cv2.INTER_CUBIC)
                variants.append(("upscaled_4x", Image.fromarray(upscaled_4x)))

            logger.info(f"Created {len(variants)} image variants for OCR")
            return variants

        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return [("original", image)]

    def _run_ocr(self, image: Any) -> str:
        """Run Tesseract OCR on image with exhaustive strategies."""
        try:
            import pytesseract

            # Try MANY configurations - slow but thorough
            # OEM 3 = Default (Legacy + LSTM)
            # OEM 1 = LSTM only (best for clean text)
            # PSM modes:
            #   3 = Fully automatic page segmentation
            #   4 = Assume single column of text
            #   6 = Assume uniform block of text
            #   11 = Sparse text
            #   12 = Sparse text with OSD

            configs = [
                # LSTM engine with different page segmentation modes
                r'--oem 1 --psm 3',   # LSTM + auto segmentation
                r'--oem 1 --psm 4',   # LSTM + single column
                r'--oem 1 --psm 6',   # LSTM + uniform block
                r'--oem 1 --psm 11',  # LSTM + sparse text
                r'--oem 1 --psm 12',  # LSTM + sparse text with OSD

                # Default engine (Legacy + LSTM)
                r'--oem 3 --psm 3',   # Default + auto segmentation
                r'--oem 3 --psm 4',   # Default + single column
                r'--oem 3 --psm 6',   # Default + uniform block
                r'--oem 3 --psm 11',  # Default + sparse text

                # Legacy engine
                r'--oem 0 --psm 3',   # Legacy + auto segmentation
                r'--oem 0 --psm 6',   # Legacy + uniform block
            ]

            results = []
            for i, config in enumerate(configs):
                try:
                    logger.info(f"Trying OCR config {i+1}/{len(configs)}: {config}")
                    text = pytesseract.image_to_string(image, config=config)
                    cleaned = text.strip()
                    if cleaned:
                        results.append(cleaned)
                        logger.info(f"Config {i+1} extracted {len(cleaned)} characters")
                except Exception as e:
                    logger.warning(f"Config {i+1} failed: {str(e)}")
                    continue

            if not results:
                logger.warning("No OCR results from any configuration")
                return ""

            # Return the longest result (usually means more text extracted)
            best = max(results, key=len)
            logger.info(f"Best result: {len(best)} characters from {len(results)} successful attempts")
            return best

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}", exc_info=True)
            return ""

    def _parse_boarding_pass_text(self, raw_text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Parse extracted text to find boarding pass fields.

        Returns:
            Tuple of (extracted_data, field_confidence)
        """
        data = {
            "flight_number": None,
            "departure_airport": None,
            "arrival_airport": None,
            "flight_date": None,
            "departure_time": None,
            "arrival_time": None,
            "passenger_name": None,
            "booking_reference": None,
            "seat_number": None,
            "airline": None,
        }
        confidence = {}

        # Normalize text for better matching
        text_upper = raw_text.upper()
        lines = text_upper.split('\n')

        # Extract flight number
        flight_match = self._find_flight_number(text_upper)
        if flight_match:
            data["flight_number"] = flight_match
            confidence["flight_number"] = 0.9

        # Extract airport codes
        airports = self._find_airport_codes(text_upper, lines)
        if airports.get("departure"):
            data["departure_airport"] = airports["departure"]
            confidence["departure_airport"] = airports.get("departure_confidence", 0.7)
        if airports.get("arrival"):
            data["arrival_airport"] = airports["arrival"]
            confidence["arrival_airport"] = airports.get("arrival_confidence", 0.7)

        # Extract date
        date_result = self._find_date(text_upper)
        if date_result:
            data["flight_date"] = date_result
            confidence["flight_date"] = 0.8

        # Extract times
        times = self._find_times(text_upper, lines)
        if times.get("departure"):
            data["departure_time"] = times["departure"]
            confidence["departure_time"] = 0.7
        if times.get("arrival"):
            data["arrival_time"] = times["arrival"]

        # Extract passenger name
        passenger = self._find_passenger_name(text_upper)
        if passenger:
            data["passenger_name"] = passenger
            confidence["passenger_name"] = 0.8

        # Extract booking reference
        booking_ref = self._find_booking_reference(text_upper)
        if booking_ref:
            data["booking_reference"] = booking_ref
            confidence["booking_reference"] = 0.7

        # Extract seat
        seat = self._find_seat(text_upper)
        if seat:
            data["seat_number"] = seat
            confidence["seat_number"] = 0.9

        return data, confidence

    def _find_flight_number(self, text: str) -> Optional[str]:
        """Find flight number in text."""
        pattern = self.PATTERNS["flight_number"]
        matches = re.findall(pattern, text)

        if matches:
            # Return first match, combining airline code and number
            airline_code, number = matches[0]
            return f"{airline_code}{number}"

        return None

    def _find_airport_codes(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """Find departure and arrival airport codes."""
        result = {}
        pattern = self.PATTERNS["airport_code"]

        # Find all 3-letter codes
        all_codes = re.findall(pattern, text)

        # Filter to likely airport codes (remove common words and boarding pass terms)
        common_words = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HAD", "HER", "WAS", "ONE", "OUR", "OUT",
            # Boarding pass terms that look like airport codes
            "DEP", "ARR", "STD", "STA", "ETD", "ETA", "ROW", "SEQ", "REF", "PNR", "MSG", "TAX", "FEE", "BAG",
        }
        airport_codes = [code for code in all_codes if code not in common_words]

        # Try to identify departure and arrival based on context
        for i, line in enumerate(lines):
            line_codes = re.findall(pattern, line)
            line_codes = [c for c in line_codes if c not in common_words]

            # Check for "FROM" context
            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["from"]):
                if line_codes:
                    result["departure"] = line_codes[0]
                    result["departure_confidence"] = 0.85

            # Check for "TO" context
            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["to"]):
                if line_codes:
                    result["arrival"] = line_codes[-1]
                    result["arrival_confidence"] = 0.85

        # If context-based detection failed, use position heuristics
        if not result.get("departure") and not result.get("arrival"):
            if len(airport_codes) >= 2:
                result["departure"] = airport_codes[0]
                result["arrival"] = airport_codes[1]
                result["departure_confidence"] = 0.6
                result["arrival_confidence"] = 0.6
            elif len(airport_codes) == 1:
                result["departure"] = airport_codes[0]
                result["departure_confidence"] = 0.5

        return result

    def _find_date(self, text: str) -> Optional[str]:
        """Find flight date in text."""
        # Try ISO format first (YYYY-MM-DD)
        iso_matches = re.findall(self.PATTERNS["date_iso"], text)
        if iso_matches:
            year, month, day = iso_matches[0]
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Try DMY format (DD/MM/YYYY or similar)
        dmy_matches = re.findall(self.PATTERNS["date_dmy"], text)
        if dmy_matches:
            day, month, year = dmy_matches[0]
            # Handle 2-digit year
            if len(year) == 2:
                year = f"20{year}" if int(year) < 50 else f"19{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return None

    def _find_times(self, text: str, lines: List[str]) -> Dict[str, str]:
        """Find departure and arrival times."""
        result = {}
        pattern = self.PATTERNS["time"]

        all_times = re.findall(pattern, text)
        formatted_times = [f"{h.zfill(2)}:{m}" for h, m in all_times if 0 <= int(h) <= 23 and 0 <= int(m) <= 59]

        # Try to identify based on context
        for line in lines:
            times_in_line = re.findall(pattern, line)
            times_in_line = [f"{h.zfill(2)}:{m}" for h, m in times_in_line if 0 <= int(h) <= 23 and 0 <= int(m) <= 59]

            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["from"] + ["DEP", "STD"]):
                if times_in_line:
                    result["departure"] = times_in_line[0]

            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["to"] + ["ARR", "STA"]):
                if times_in_line:
                    result["arrival"] = times_in_line[0]

        # Fallback: first two times
        if not result.get("departure") and formatted_times:
            result["departure"] = formatted_times[0]
        if not result.get("arrival") and len(formatted_times) >= 2:
            result["arrival"] = formatted_times[1]

        return result

    def _find_passenger_name(self, text: str) -> Optional[str]:
        """Find passenger name in LASTNAME/FIRSTNAME format."""
        pattern = self.PATTERNS["passenger_name"]
        matches = re.findall(pattern, text)

        if matches:
            lastname, firstname = matches[0]
            # Clean up and format
            return f"{lastname}/{firstname}"

        return None

    def _find_booking_reference(self, text: str) -> Optional[str]:
        """Find 6-character booking reference."""
        pattern = self.PATTERNS["booking_ref"]

        # Look for booking reference near context keywords
        for line in text.split('\n'):
            if any(kw.upper() in line.upper() for kw in self.CONTEXT_KEYWORDS["booking"]):
                matches = re.findall(pattern, line)
                if matches:
                    return matches[0]

        # Fallback: find any 6-char alphanumeric that's not a common word
        all_matches = re.findall(pattern, text)
        for match in all_matches:
            # Filter out likely false positives
            if not match.isdigit() and not match.isalpha():
                return match
            if match.isalpha() and len(set(match)) > 2:  # Has variety in letters
                return match

        return None

    def _find_seat(self, text: str) -> Optional[str]:
        """Find seat number."""
        pattern = self.PATTERNS["seat"]

        # Look for seat near context keywords
        for line in text.split('\n'):
            if any(kw.upper() in line.upper() for kw in self.CONTEXT_KEYWORDS["seat"]):
                matches = re.findall(pattern, line)
                if matches:
                    row, letter = matches[0]
                    return f"{row}{letter}"

        return None

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate extracted data against known values.

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        # Validate airport codes if available
        if data.get("departure_airport"):
            if not self._is_valid_airport(data["departure_airport"]):
                warnings.append(f"Departure airport '{data['departure_airport']}' may not be valid")

        if data.get("arrival_airport"):
            if not self._is_valid_airport(data["arrival_airport"]):
                warnings.append(f"Arrival airport '{data['arrival_airport']}' may not be valid")

        # Check if essential fields are present
        if not data.get("flight_number"):
            warnings.append("Could not extract flight number")

        if not data.get("departure_airport") and not data.get("arrival_airport"):
            warnings.append("Could not extract airport codes")

        if not data.get("flight_date"):
            warnings.append("Could not extract flight date")

        return errors, warnings

    def _is_valid_airport(self, code: str) -> bool:
        """Check if airport code is valid using airport database."""
        try:
            from app.services.airport_database_service import AirportDatabaseService

            AirportDatabaseService.load_database()
            results = AirportDatabaseService.search(code, limit=1)

            if results and results[0].get("iata") == code:
                return True

        except Exception as e:
            logger.debug(f"Airport validation skipped: {str(e)}")

        return False

    def _calculate_overall_confidence(self, field_confidence: Dict[str, float]) -> float:
        """Calculate overall confidence score from individual field scores."""
        if not field_confidence:
            return 0.0

        # Weight important fields more heavily
        weights = {
            "flight_number": 1.5,
            "departure_airport": 1.2,
            "arrival_airport": 1.2,
            "flight_date": 1.0,
            "departure_time": 0.8,
            "passenger_name": 0.8,
            "booking_reference": 0.5,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for field, confidence in field_confidence.items():
            weight = weights.get(field, 0.5)
            weighted_sum += confidence * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 2)


# Global service instance
ocr_service = OCRService()
