"""
OCR Service for extracting flight data from boarding pass images.

Uses Google Cloud Vision API for high-quality OCR with barcode reading fallback.
"""

import io
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from app.services.cache_service import CacheService
from app.tasks.admin_tasks import send_admin_alert_email

logger = logging.getLogger(__name__)


class OCRService:
    """
    Extract flight data from boarding pass images using:
    1. Barcode/QR code reading (pyzbar) - Free, instant, 100% accurate
    2. Google Cloud Vision API - Premium OCR, $1.50/1000 images

    Supports:
    - JPEG, PNG, WebP images
    - PDF documents (first page)
    - Barcode extraction (PDF417, QR, DataMatrix, Aztec)
    """

    # Major airline IATA codes for validation
    KNOWN_AIRLINES = {
        'AA': 'American Airlines', 'AC': 'Air Canada', 'AF': 'Air France',
        'BA': 'British Airways', 'DL': 'Delta', 'EK': 'Emirates',
        'EY': 'Etihad', 'IB': 'Iberia', 'KL': 'KLM', 'LH': 'Lufthansa',
        'LX': 'Swiss', 'NH': 'ANA', 'OS': 'Austrian', 'QF': 'Qantas',
        'QR': 'Qatar Airways', 'SQ': 'Singapore Airlines', 'TK': 'Turkish',
        'UA': 'United', 'VS': 'Virgin Atlantic', 'WN': 'Southwest',
        'FR': 'Ryanair', 'U2': 'easyJet', 'VY': 'Vueling', 'W6': 'Wizz Air',
        'AZ': 'ITA Airways', 'LO': 'LOT Polish', 'SK': 'SAS', 'TP': 'TAP Portugal',
        'AV': 'Avianca', 'JJ': 'LATAM', 'LA': 'LATAM', 'IB': 'Iberia',
        'UX': 'Air Europa', 'EI': 'Aer Lingus', 'AY': 'Finnair', 'SU': 'Aeroflot',
        'JL': 'Japan Airlines', 'KE': 'Korean Air', 'CX': 'Cathay Pacific',
    }

    # Regex patterns for extracting boarding pass data
    PATTERNS = {
        # Relaxed flight number to catch spaces (e.g. "L H 1234") and alphanumeric flight numbers
        "flight_number": r"\b([A-Z0-9]{2})\s*([0-9][A-Z0-9]{0,4})\b",
        "airport_code": r"\b([A-Z]{3})\b",
        "date_dmy": r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b",
        "date_iso": r"\b(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})\b",
        # Relaxed compact date to allow spaces (27 JUN 2022)
        "date_compact": r"\b(\d{1,2})\s*[-/.]?\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[-/.]?\s*(\d{2,4})\b",
        "time": r"\b(\d{1,2}):(\d{2})\b",
        "booking_ref": r"\b([A-Z0-9]{5,6})\b",
        # Support SURNAME/NAME, SURNAME, NAME and NAME SURNAME formats
        # Prevent newline matching in separator by using [ \t] instead of \s
        "passenger_name": r"([A-Z][A-Z\-\ \t]*)(?:/|,\s*|[ \t]+)([A-Z][A-Z\-\ \t]*)",
        "seat": r"\b(\d{1,2})\s*([A-F])\b",
    }

    CONTEXT_KEYWORDS = {
        "flight": ["flight", "flug", "vol", "vuelo", "volo", "flt"],
        "from": ["from", "departure", "dep", "von", "depart", "origin", "dprt"],
        "to": ["to", "arrival", "arr", "nach", "dest", "destination", "arvl"],
        "date": ["date", "datum", "fecha", "data"],
        "time": ["time", "zeit", "hora", "ora", "boarding", "board", "brd"],
        "gate": ["gate", "tor", "puerta", "porta"],
        "seat": ["seat", "sitz", "asiento", "posto", "place"],
        "passenger": ["passenger", "passagier", "pasajero", "passeggero", "name", "pax"],
        "booking": ["booking", "buchung", "reserva", "prenotazione", "pnr", "confirmation", "conf"],
    }

    MONTH_MAP = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
    }

    def __init__(self):
        """Initialize OCR service."""
        self._pyzbar_available = None
        self._google_vision_available = None
        self._google_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        logger.info(f"OCRService initialized. Credentials path: {self._google_credentials_path}")

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if OCR dependencies are available."""
        status = {}

        try:
            import pyzbar
            status["pyzbar"] = True
        except ImportError:
            status["pyzbar"] = False

        try:
            from google.cloud import vision
            if self._google_credentials_path and os.path.exists(self._google_credentials_path):
                status["google_vision"] = True
            else:
                try:
                    client = vision.ImageAnnotatorClient()
                    status["google_vision"] = True
                except Exception:
                    status["google_vision"] = False
        except ImportError:
            status["google_vision"] = False

        return status

    async def extract_boarding_pass_data(
        self,
        file_content: bytes,
        mime_type: str,
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """Extract flight details from boarding pass image."""
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
            "extraction_method": None,
        }

        try:
            deps = self._check_dependencies()
            image = await self._load_image(file_content, mime_type)
            
            if image is None:
                result["errors"].append(f"Failed to load image from {mime_type} file")
                return result

            # STEP 1: Try barcode reading first
            if deps.get("pyzbar"):
                logger.info("Attempting barcode/QR code reading...")
                barcode_data = self._decode_barcode(image)

                if barcode_data:
                    logger.info(f"Successfully decoded barcode: {barcode_data['type']}")
                    result["raw_text"] = barcode_data["raw_data"]
                    result["extraction_method"] = f"barcode_{barcode_data['type']}"

                    extracted_data, field_confidence = self._parse_barcode_data(
                        barcode_data["data"], barcode_data["type"]
                    )

                    if extracted_data and any(v is not None for v in extracted_data.values()):
                        result["success"] = True
                        result["data"] = extracted_data
                        result["field_confidence"] = field_confidence
                        result["confidence_score"] = self._calculate_overall_confidence(field_confidence)
                        result["processing_time_ms"] = int((time.time() - start_time) * 1000)
                        return result
                else:
                    logger.info("No barcode found, falling back to Google Vision OCR")
                    result["warnings"].append("No machine-readable barcode found, using cloud OCR")

            # STEP 2: Fall back to Google Cloud Vision API
            if not deps.get("google_vision"):
                result["errors"].append(
                    "Google Cloud Vision API not configured. "
                    "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )
                return result

            logger.info("Starting Google Cloud Vision OCR...")
            result["extraction_method"] = "google_vision_api"

            ocr_text = await self._run_google_vision_ocr(file_content)

            if not ocr_text or len(ocr_text.strip()) < 10:
                result["errors"].append("Google Vision could not extract text from image")
                return result

            logger.info(f"Google Vision extracted {len(ocr_text)} characters")
            result["raw_text"] = ocr_text

            extracted_data, field_confidence = self._parse_boarding_pass_text(ocr_text)
            field_count = sum(1 for v in extracted_data.values() if v is not None)
            
            logger.info(f"Parsed {field_count} fields from Google Vision text")

            if field_count == 0:
                result["errors"].append("Could not parse boarding pass data from extracted text")
                return result

            validation_errors, validation_warnings = self._validate_extracted_data(extracted_data)
            result["warnings"].extend(validation_warnings + validation_errors)

            overall_confidence = self._calculate_overall_confidence(field_confidence)

            result["success"] = True
            result["data"] = extracted_data
            result["field_confidence"] = field_confidence
            result["confidence_score"] = overall_confidence

            if overall_confidence < 0.5:
                result["warnings"].append("Low confidence extraction - please verify all fields manually")
            elif overall_confidence < 0.7:
                result["warnings"].append("Some fields may need verification")

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
            result["errors"].append(f"OCR processing error: {str(e)}")

        finally:
            result["processing_time_ms"] = int((time.time() - start_time) * 1000)

        return result

    async def _load_image(self, file_content: bytes, mime_type: str) -> Optional[Any]:
        """Load image from file content."""
        try:
            from PIL import Image
            if mime_type in ["image/jpeg", "image/png", "image/webp"]:
                return Image.open(io.BytesIO(file_content))
            elif mime_type == "application/pdf":
                return file_content
            return None
        except Exception as e:
            logger.error(f"Failed to load image: {str(e)}", exc_info=True)
            return None

    async def _check_and_increment_usage(self) -> bool:
        """
        Check and increment Google Vision API usage counter.
        
        Enforces a strict limit of 999 requests per month (Free tier limit).
        Sends an alert email when usage reaches 900.
        
        Returns:
            True if usage is within limit, False if limit exceeded.
        """
        try:
            client = await CacheService.get_redis_client()
            if not client:
                logger.warning("Redis unavailable, proceeding without usage tracking (risk of overage)")
                return True

            # Monthly key format: ocr:usage:2026-01
            current_month = datetime.now().strftime("%Y-%m")
            usage_key = f"ocr:usage:{current_month}"
            warning_key = f"ocr:warning_sent:{current_month}"
            
            # Get current usage (atomic increment)
            current_usage = await client.incr(usage_key)
            
            # Set expiry for 40 days (auto-cleanup) if new key
            if current_usage == 1:
                await client.expire(usage_key, 60 * 60 * 24 * 40)

            logger.info(f"Google Vision API usage for {current_month}: {current_usage}/999")

            # Check Hard Limit (999)
            if current_usage > 999:
                logger.error(f"Google Vision API monthly limit reached ({current_usage}/999). Blocking request.")
                return False

            # Check Warning Threshold (900)
            if current_usage >= 900:
                warning_sent = await client.get(warning_key)
                if not warning_sent:
                    logger.warning(f"Google Vision API usage reached warning threshold ({current_usage}/999). Sending alert.")
                    
                    # Send alert email
                    send_admin_alert_email.delay(
                        subject=f"Action Required: Google Vision API Limit Warning ({current_usage}/999)",
                        message=f"Google Vision API usage has reached {current_usage} requests for {current_month}.\n\n"
                                f"The hard limit is set to 999 to prevent billing charges.\n"
                                f"Please review usage or increase the limit if needed."
                    )
                    
                    # Mark warning as sent (expire after 40 days)
                    await client.setex(warning_key, 60 * 60 * 24 * 40, "1")

            return True

        except Exception as e:
            logger.error(f"Error checking usage limit: {str(e)}", exc_info=True)
            # Default to allow if tracking fails, to avoid breaking service on Redis error
            return True

    async def _run_google_vision_ocr(self, file_content: bytes) -> str:
        """Run Google Cloud Vision API OCR."""
        try:
            # Check monthly usage limit first
            if not await self._check_and_increment_usage():
                raise Exception("Monthly OCR usage limit reached (999). Please try again next month or contact support.")

            from google.cloud import vision
            from google.api_core.exceptions import PermissionDenied
            
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=file_content)
            
            # Use document text detection with language hints for better accuracy
            image_context = vision.ImageContext(language_hints=["en"])
            response = client.document_text_detection(image=image, image_context=image_context)

            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")

            text = ""
            if response.full_text_annotation:
                text = response.full_text_annotation.text
            elif response.text_annotations:
                text = response.text_annotations[0].description if response.text_annotations else ""
            
            # Log the first 500 characters of extracted text for debugging quality issues
            if text:
                logger.info(f"OCR Raw Text Sample (first 500 chars):\n{text[:500]}...")
            else:
                logger.warning("OCR returned empty text.")
                
            return text
        except ImportError:
            logger.error("Google Cloud Vision library not installed")
            raise
        except Exception as e:
            # Handle PermissionDenied specifically (billing issues)
            if "PermissionDenied" in str(type(e)) or "billing" in str(e).lower():
                logger.error(f"Google Vision Billing Error: {str(e)}")
                raise Exception("Google Cloud Billing is not enabled for this project. Please enable billing in Google Cloud Console.")
            
            logger.error(f"Google Vision OCR failed: {str(e)}", exc_info=True)
            raise

    def _decode_barcode(self, image: Any) -> Optional[Dict[str, Any]]:
        """Decode barcode/QR code from image."""
        try:
            from pyzbar import pyzbar
            import numpy as np

            if isinstance(image, bytes):
                return None

            img_array = np.array(image)
            decoded_objects = pyzbar.decode(img_array)

            if not decoded_objects:
                return None

            barcode = decoded_objects[0]
            raw_data = barcode.data.decode('utf-8', errors='ignore')
            
            return {
                "type": barcode.type,
                "raw_data": raw_data,
                "data": raw_data,
            }
        except Exception as e:
            logger.warning(f"Barcode decoding failed: {str(e)}")
            return None

    def _parse_barcode_data(self, data: str, barcode_type: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Parse IATA BCBP format from barcode."""
        extracted = {
            "flight_number": None, "departure_airport": None, "arrival_airport": None,
            "flight_date": None, "departure_time": None, "arrival_time": None,
            "passenger_name": None, "booking_reference": None, "seat_number": None, "airline": None,
        }
        confidence = {}

        try:
            if barcode_type == "PDF417" and len(data) >= 60 and data[0] == 'M':
                name_field = data[2:22].strip()
                if '/' in name_field:
                    extracted["passenger_name"] = name_field
                    confidence["passenger_name"] = 0.95

                pnr = data[23:29].strip()
                if pnr and pnr.isalnum():
                    extracted["booking_reference"] = pnr
                    confidence["booking_reference"] = 0.95

                from_airport = data[30:33].strip()
                if from_airport and from_airport.isalpha() and len(from_airport) == 3:
                    extracted["departure_airport"] = from_airport
                    confidence["departure_airport"] = 0.95

                to_airport = data[34:37].strip()
                if to_airport and to_airport.isalpha() and len(to_airport) == 3:
                    extracted["arrival_airport"] = to_airport
                    confidence["arrival_airport"] = 0.95

                airline_flight = data[38:45].strip()
                if len(airline_flight) >= 4:
                    airline_code = airline_flight[:3].rstrip('0123456789')
                    flight_num = airline_flight[len(airline_code):].lstrip('0')
                    if airline_code and flight_num:
                        extracted["flight_number"] = f"{airline_code}{flight_num}"
                        extracted["airline"] = self.KNOWN_AIRLINES.get(airline_code, airline_code)
                        confidence["flight_number"] = 0.95

                seat = data[47:51].strip()
                if seat and len(seat) >= 2:
                    extracted["seat_number"] = seat
                    confidence["seat_number"] = 0.90

            if not any(v is not None for v in extracted.values()):
                extracted, confidence = self._parse_boarding_pass_text(data)

        except Exception as e:
            logger.warning(f"Barcode parsing failed: {str(e)}")

        return extracted, confidence

    def _parse_boarding_pass_text(self, raw_text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Parse text to find boarding pass fields."""
        data = {
            "flight_number": None, "departure_airport": None, "arrival_airport": None,
            "flight_date": None, "departure_time": None, "arrival_time": None,
            "passenger_name": None, "booking_reference": None, "seat_number": None, "airline": None,
        }
        confidence = {}

        text_upper = raw_text.upper()
        lines = text_upper.split('\n')

        flight_match = self._find_flight_number(text_upper)
        if flight_match:
            data["flight_number"] = flight_match
            airline_code = flight_match[:2]
            if airline_code in self.KNOWN_AIRLINES:
                data["airline"] = self.KNOWN_AIRLINES[airline_code]
                confidence["flight_number"] = 0.9
            else:
                confidence["flight_number"] = 0.7

        airports = self._find_airport_codes(text_upper, lines)
        if airports.get("departure"):
            data["departure_airport"] = airports["departure"]
            confidence["departure_airport"] = airports.get("departure_confidence", 0.7)
        if airports.get("arrival"):
            data["arrival_airport"] = airports["arrival"]
            confidence["arrival_airport"] = airports.get("arrival_confidence", 0.7)

        date_result = self._find_date(text_upper)
        if date_result:
            data["flight_date"] = date_result
            confidence["flight_date"] = 0.8

        times = self._find_times(text_upper, lines)
        if times.get("departure"):
            data["departure_time"] = times["departure"]
            confidence["departure_time"] = 0.7
        if times.get("arrival"):
            data["arrival_time"] = times["arrival"]

        passenger = self._find_passenger_name(text_upper)
        if passenger:
            data["passenger_name"] = passenger
            confidence["passenger_name"] = 0.8

        booking_ref = self._find_booking_reference(text_upper, data.get("flight_number"), data.get("passenger_name"))
        if booking_ref:
            data["booking_reference"] = booking_ref
            confidence["booking_reference"] = 0.7

        seat = self._find_seat(text_upper)
        if seat:
            data["seat_number"] = seat
            confidence["seat_number"] = 0.9

        return data, confidence

    def _find_flight_number(self, text: str) -> Optional[str]:
        pattern = self.PATTERNS["flight_number"]
        matches = re.findall(pattern, text)
        for airline_code, number in matches:
            if airline_code in self.KNOWN_AIRLINES:
                return f"{airline_code}{number}"
        if matches:
            return f"{matches[0][0]}{matches[0][1]}"
        return None

    def _find_airport_codes(self, text: str, lines: List[str]) -> Dict[str, Any]:
        result = {}
        pattern = self.PATTERNS["airport_code"]
        all_codes = re.findall(pattern, text)
        common_words = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HAD", "HER", "WAS", "ONE", "OUR", "OUT",
            "DEP", "ARR", "STD", "STA", "ETD", "ETA", "ROW", "SEQ", "REF", "PNR", "MSG", "TAX", "FEE", "BAG",
            "BRD", "GTE", "FLT", "PAX", "CLS", "CLA", "ECO", "BUS", "FST",
            "GRP", "SEC", "PRN", "TKT", "GATE", "SITZ", "SEAT", "ZONE", "GROUP", "STATUS", "MEMBER",
            "PRE", "GAP", "AIR"  # Add PRE (often Group/Premium) to blocklist
        }
        airport_codes = [code for code in all_codes if code not in common_words]

        for line in lines:
            line_codes = re.findall(pattern, line)
            line_codes = [c for c in line_codes if c not in common_words]
            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["from"]):
                if line_codes:
                    result["departure"] = line_codes[0]
                    result["departure_confidence"] = 0.85
            if any(kw.upper() in line for kw in self.CONTEXT_KEYWORDS["to"]):
                if line_codes:
                    result["arrival"] = line_codes[-1]
                    result["arrival_confidence"] = 0.85

        if not result.get("departure") and not result.get("arrival"):
            # Filter out months and common names from fallback candidates
            filtered_codes = []
            months = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
            names = {"DOE", "JON", "DAN", "TOM", "PAT", "LEO", "SAM", "JIM", "TIM", "RON", "BEN", "MAX", "RAY"}
            
            for code in airport_codes:
                if code in months:
                    continue
                if code in names:
                    continue
                filtered_codes.append(code)
                
            if len(filtered_codes) >= 2:
                result["departure"] = filtered_codes[0]
                result["arrival"] = filtered_codes[1]
                result["departure_confidence"] = 0.6
                result["arrival_confidence"] = 0.6

        return result

    def _find_date(self, text: str) -> Optional[str]:
        compact_matches = re.findall(self.PATTERNS["date_compact"], text)
        if compact_matches:
            day, month, year = compact_matches[0]
            month_num = self.MONTH_MAP.get(month)
            if month_num:
                # Handle 2-digit and 4-digit years
                if len(year) == 4:
                    year_full = year
                else:
                    year_full = f"20{year}" if int(year) < 50 else f"19{year}"
                return f"{year_full}-{month_num}-{day.zfill(2)}"

        iso_matches = re.findall(self.PATTERNS["date_iso"], text)
        if iso_matches:
            year, month, day = iso_matches[0]
            if len(year) == 2: # Should not happen with \d{4} regex but good for safety
                 year = f"20{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        dmy_matches = re.findall(self.PATTERNS["date_dmy"], text)
        if dmy_matches:
            day, month, year = dmy_matches[0]
            if len(year) == 4:
                year_full = year
            else:
                year_full = f"20{year}" if int(year) < 50 else f"19{year}"
            return f"{year_full}-{month_num}-{day.zfill(2)}" if 'month_num' in locals() else f"{year_full}-{month.zfill(2)}-{day.zfill(2)}"

        return None

    def _find_times(self, text: str, lines: List[str]) -> Dict[str, str]:
        result = {}
        pattern = self.PATTERNS["time"]
        
        # Helper to check proximity to keywords
        def is_near_keyword(line: str, keywords: List[str]) -> bool:
            return any(kw.upper() in line for kw in keywords)

        # First pass: Look for times on the same line as keywords
        for line in lines:
            times_in_line = re.findall(pattern, line)
            times_in_line = [f"{h.zfill(2)}:{m}" for h, m in times_in_line if 0 <= int(h) <= 23 and 0 <= int(m) <= 59]
            
            if not times_in_line:
                continue

            if is_near_keyword(line, self.CONTEXT_KEYWORDS["from"] + ["DEP", "STD", "BOARD", "ABFLUG"]):
                result["departure"] = times_in_line[0]
            
            if is_near_keyword(line, self.CONTEXT_KEYWORDS["to"] + ["ARR", "STA", "ANKUNFT", "DEST"]):
                result["arrival"] = times_in_line[-1]

        # Second pass: If still missing, look at all times but ignore first few lines (often status bar)
        if not result.get("departure") or not result.get("arrival"):
            all_times = []
            for i, line in enumerate(lines):
                # Skip first 2 lines to avoid phone status bar times (e.g., 15:16)
                if i < 2:
                    continue
                    
                # Ignore lines with Gate Close or Boarding keywords for Arrival time candidate
                is_boarding_line = any(kw in line.upper() for kw in ["BOARDING", "GATE", "SCHLIESST", "CLOSE", "DEPART", "ABFLUG"])
                
                matches = re.findall(pattern, line)
                for h, m in matches:
                    if 0 <= int(h) <= 23 and 0 <= int(m) <= 59:
                        all_times.append({"time": f"{h.zfill(2)}:{m}", "is_boarding": is_boarding_line})

            if not result.get("departure") and all_times:
                result["departure"] = all_times[0]["time"]
            
            if not result.get("arrival") and len(all_times) >= 2:
                candidate = all_times[1]
                if not candidate["is_boarding"]:
                    # Check duration if we have both times
                    dep_time = result.get("departure")
                    arr_time = candidate["time"]
                    
                    if dep_time and arr_time:
                        try:
                            # Simple check: if difference is < 30 mins, likely not a flight
                            # Handle HH:MM
                            dep_h, dep_m = map(int, dep_time.split(':'))
                            arr_h, arr_m = map(int, arr_time.split(':'))
                            
                            dep_mins = dep_h * 60 + dep_m
                            arr_mins = arr_h * 60 + arr_m
                            
                            # Handle date rollover (arrival next day) - usually arrival > dep
                            # If arr < dep (next day), diff is (24*60 + arr) - dep
                            # But here we are worried about small positive diffs (e.g. 08:00 -> 08:15)
                            
                            diff = arr_mins - dep_mins
                            if 0 < diff < 45: # Less than 45 mins flight is very rare (usually gate close)
                                pass # Ignore this candidate as arrival
                            else:
                                result["arrival"] = arr_time
                        except:
                            result["arrival"] = arr_time
                    else:
                        result["arrival"] = arr_time

        return result

    def _find_passenger_name(self, text: str) -> Optional[str]:
        pattern = self.PATTERNS["passenger_name"]
        
        # Blocklist for words that indicate end of name
        name_blocklist = [
            "PASSAGIER", "PASSENGER", "NAME", "KLASSE", "CLASS", "STATUS", "ECONOMY", "BUSINESS", 
            "FIRST", "M/M", "MR", "MRS", "MS", "BOARDING", "PASS", "TICKET", "FLIGHT", "GRP", 
            "SITZ", "SEAT", "PRE", "SEC", "NO", "GATE", "ZONE", "GROUP"
        ]
        
        # Helper to clean and validate name
        def validate_name(surname, firstname):
             # Clean up
            surname = surname.strip().replace('\n', ' ')
            firstname = firstname.strip().replace('\n', ' ')
            
            # Truncate at any blocklist word (case insensitive check)
            for blocked in name_blocklist:
                # Check surname
                idx = surname.upper().find(blocked)
                if idx != -1:
                    surname = surname[:idx].strip()
                
                # Check firstname
                idx = firstname.upper().find(blocked)
                if idx != -1:
                    firstname = firstname[:idx].strip()

            full_str = f"{surname} {firstname}".upper()
            
            if "AIRLINES" in full_str or "AIRWAYS" in full_str:
                return None
            
            # Ensure we still have a valid name after truncation
            if len(surname) < 2 or len(firstname) < 2:
                return None
            
            # Check if name contains digits (invalid)
            if any(char.isdigit() for char in full_str):
                return None
            
            # Check if it matches any blocklist word exactly
            if surname.upper() in name_blocklist or firstname.upper() in name_blocklist:
                return None
                
            return f"{surname}/{firstname}"

        # 1. First Pass: Look for names near "PASSENGER" keywords
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(kw.upper() in line.upper() for kw in self.CONTEXT_KEYWORDS["passenger"]):
                # Check this line and next 4 lines (names often appear below labels)
                for offset in range(5):
                    if i + offset >= len(lines):
                        break
                    
                    matches = re.findall(pattern, lines[i + offset])
                    for s, f in matches:
                        valid = validate_name(s, f)
                        if valid:
                            return valid

        # 2. Second Pass: Global search
        matches = re.findall(pattern, text)
        for surname, firstname in matches:
            valid = validate_name(surname, firstname)
            if valid:
                return valid

        return None

    def _find_booking_reference(self, text: str, flight_number: Optional[str] = None, passenger_name: Optional[str] = None) -> Optional[str]:
        pattern = self.PATTERNS["booking_ref"]
        # Words to ignore (false positives)
        ignore_words = {
            "DATUM", "FLIGHT", "BOARD", "CLASS", "SEAT", "GATE", "ENTRY", "GROUP", "ZONE", 
            "START", "FIRST", "PRIOR", "ECONO", "BUSIN", "WORLD", "MILES", "EXTRA", "TOTAL", 
            "TAXES", "FARES", "PHONE", "EMAIL", "STATUS", "MEMBER", "SHORT", "LABEL", "INDEX",
            "PRINT", "CHECK", "IN", "OUT", "PASS", "NAME", "DATE", "TIME", "FROM", "DEST",
            "SYDNEY", "PARIS", "MADRID", "LONDON", "ROME", "BERLIN", "MUNICH", "MUNCHEN", 
            "MÜNCHEN", "BARAJAS", "HEATHROW", "GATWICK", "KENNEDY", "NEWARK", "ORLY", "KLASSE"
        }
        
        for line in text.split('\n'):
            if any(kw.upper() in line.upper() for kw in self.CONTEXT_KEYWORDS["booking"]):
                matches = re.findall(pattern, line)
                if matches:
                    candidate = matches[0]
                    if candidate not in ignore_words:
                        return candidate
                        
        all_matches = re.findall(pattern, text)
        for match in all_matches:
            if flight_number and match in flight_number:
                continue
            if passenger_name and match in passenger_name.upper():
                continue
            if match in ignore_words:
                continue
            if not match.isdigit() and len(set(match)) > 2:
                return match
        return None

    def _find_seat(self, text: str) -> Optional[str]:
        pattern = self.PATTERNS["seat"]
        # Prioritize lines with "SEAT" or "SITZ"
        for line in text.split('\n'):
            if any(kw.upper() in line.upper() for kw in self.CONTEXT_KEYWORDS["seat"]):
                matches = re.findall(pattern, line)
                if matches:
                    return f"{matches[0][0]}{matches[0][1]}"
        
        # Fallback: Look for the pattern anywhere, but ignore "K14" or "15:16" false positives
        all_matches = re.findall(pattern, text)
        for num, letter in all_matches:
            # Filter out things that might be time parts or gates like K14 (K is not A-F)
            # Regex only allows A-F so K14 is already excluded.
            # But what about "15:16"? "15" and ":", no match. "16" and "?".
            return f"{num}{letter}"
            
        return None

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        errors, warnings = [], []
        if data.get("departure_airport") and not self._is_valid_airport(data["departure_airport"]):
            warnings.append(f"Departure airport '{data['departure_airport']}' may not be valid")
        if data.get("arrival_airport") and not self._is_valid_airport(data["arrival_airport"]):
            warnings.append(f"Arrival airport '{data['arrival_airport']}' may not be valid")
        if not data.get("flight_number"):
            warnings.append("Could not extract flight number")
        if not data.get("departure_airport") and not data.get("arrival_airport"):
            warnings.append("Could not extract airport codes")
        if not data.get("flight_date"):
            warnings.append("Could not extract flight date")
        return errors, warnings

    def _is_valid_airport(self, code: str) -> bool:
        try:
            from app.services.airport_database_service import AirportDatabaseService
            AirportDatabaseService.load_database()
            results = AirportDatabaseService.search(code, limit=1)
            return bool(results and results[0].get("iata") == code)
        except Exception:
            return False

    def _calculate_overall_confidence(self, field_confidence: Dict[str, float]) -> float:
        if not field_confidence:
            return 0.0
        weights = {
            "flight_number": 1.5, "departure_airport": 1.2, "arrival_airport": 1.2,
            "flight_date": 1.0, "departure_time": 0.8, "passenger_name": 0.8, "booking_reference": 0.5,
        }
        total_weight = weighted_sum = 0.0
        for field, confidence in field_confidence.items():
            weight = weights.get(field, 0.5)
            weighted_sum += confidence * weight
            total_weight += weight
        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


ocr_service = OCRService()
