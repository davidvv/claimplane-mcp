"""Compensation calculation service based on EU Regulation 261/2004."""
import logging
import math
from decimal import Decimal
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

from app.services.aerodatabox_service import AeroDataBoxService
from app.exceptions import AeroDataBoxError

logger = logging.getLogger(__name__)


# Airport coordinates database (partial - to be expanded)
AIRPORT_COORDINATES = {
    # Major European airports
    "LHR": (51.4700, -0.4543),    # London Heathrow
    "CDG": (49.0097, 2.5479),      # Paris Charles de Gaulle
    "FRA": (50.0379, 8.5622),      # Frankfurt
    "AMS": (52.3105, 4.7683),      # Amsterdam Schiphol
    "MAD": (40.4719, -3.5626),     # Madrid
    "BCN": (41.2974, 2.0833),      # Barcelona
    "FCO": (41.8003, 12.2389),     # Rome Fiumicino
    "MUC": (48.3538, 11.7861),     # Munich
    "IST": (41.2753, 28.7519),     # Istanbul
    "DUB": (53.4213, -6.2701),     # Dublin

    # North American airports
    "JFK": (40.6413, -73.7781),    # New York JFK
    "LAX": (33.9416, -118.4085),   # Los Angeles
    "ORD": (41.9742, -87.9073),    # Chicago O'Hare
    "ATL": (33.6407, -84.4277),    # Atlanta
    "MIA": (25.7959, -80.2870),    # Miami
    "YYZ": (43.6777, -79.6248),    # Toronto

    # Asian airports
    "DXB": (25.2532, 55.3657),     # Dubai
    "HKG": (22.3080, 113.9185),    # Hong Kong
    "SIN": (1.3644, 103.9915),     # Singapore
    "NRT": (35.7653, 140.3863),    # Tokyo Narita
    "PEK": (40.0799, 116.6031),    # Beijing

    # Add more airports as needed
}


class CompensationService:
    """Service for calculating flight compensation based on EU261/2004."""

    # Compensation tiers based on distance (in EUR)
    TIER_SHORT_HAUL = 250        # < 1,500 km
    TIER_MEDIUM_HAUL = 400       # 1,500 - 3,500 km
    TIER_LONG_HAUL = 600         # > 3,500 km

    # Distance thresholds (in km)
    SHORT_HAUL_THRESHOLD = 1500
    MEDIUM_HAUL_THRESHOLD = 3500

    # Delay thresholds (in hours)
    MIN_DELAY_FOR_COMPENSATION = 3.0
    PARTIAL_COMPENSATION_THRESHOLD = 4.0  # For long haul flights

    # Extraordinary circumstances keywords
    EXTRAORDINARY_CIRCUMSTANCES_KEYWORDS = [
        "weather", "storm", "snow", "ice", "fog", "hurricane",
        "political", "security", "strike", "air traffic control",
        "atc", "bird strike", "volcanic ash", "war", "terrorism"
    ]

    @staticmethod
    async def calculate_distance(
        departure_airport: str,
        arrival_airport: str,
        use_api: bool = True
    ) -> Optional[float]:
        """
        Calculate great circle distance between two airports in kilometers.

        Attempts multiple methods in order:
        1. AeroDataBox API (if use_api=True) - supports all airports
        2. Hardcoded AIRPORT_COORDINATES - fallback for common airports
        3. Returns None if airport coordinates cannot be found

        Args:
            departure_airport: IATA code of departure airport
            arrival_airport: IATA code of arrival airport
            use_api: Whether to try AeroDataBox API first (default: True)

        Returns:
            Distance in kilometers, or None if airport coordinates not found
        """
        departure_airport = departure_airport.upper()
        arrival_airport = arrival_airport.upper()

        # Method 1: Try AeroDataBox API first (if enabled)
        if use_api:
            try:
                aerodatabox_service = AeroDataBoxService()
                distance = await aerodatabox_service.calculate_flight_distance(
                    departure_airport,
                    arrival_airport
                )
                logger.info(
                    f"Distance from {departure_airport} to {arrival_airport}: {distance:.2f} km (via AeroDataBox API)"
                )
                return distance
            except AeroDataBoxError as e:
                logger.warning(
                    f"AeroDataBox API failed for {departure_airport}-{arrival_airport}: {str(e)}. "
                    "Falling back to hardcoded coordinates."
                )
            except Exception as e:
                logger.warning(
                    f"Unexpected error calling AeroDataBox API: {str(e)}. "
                    "Falling back to hardcoded coordinates."
                )

        # Method 2: Fallback to hardcoded coordinates
        departure_coords = AIRPORT_COORDINATES.get(departure_airport)
        arrival_coords = AIRPORT_COORDINATES.get(arrival_airport)

        if departure_coords and arrival_coords:
            # Haversine formula for great circle distance
            lat1, lon1 = map(math.radians, departure_coords)
            lat2, lon2 = map(math.radians, arrival_coords)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))

            # Earth's radius in kilometers
            earth_radius_km = 6371

            distance = earth_radius_km * c

            logger.info(
                f"Distance from {departure_airport} to {arrival_airport}: {distance:.2f} km (via hardcoded coordinates)"
            )
            return distance

        # Method 3: No coordinates found
        logger.warning(
            f"Airport coordinates not found for {departure_airport} or {arrival_airport} "
            "(neither via API nor hardcoded database)"
        )
        return None

    @staticmethod
    def get_base_compensation(distance_km: float) -> Decimal:
        """
        Get base compensation amount based on flight distance.

        Args:
            distance_km: Flight distance in kilometers

        Returns:
            Base compensation amount in EUR
        """
        if distance_km < CompensationService.SHORT_HAUL_THRESHOLD:
            return Decimal(str(CompensationService.TIER_SHORT_HAUL))
        elif distance_km < CompensationService.MEDIUM_HAUL_THRESHOLD:
            return Decimal(str(CompensationService.TIER_MEDIUM_HAUL))
        else:
            return Decimal(str(CompensationService.TIER_LONG_HAUL))

    @staticmethod
    def _get_distance_tier(distance_km: float) -> str:
        """
        Get the distance tier category for a flight.

        Args:
            distance_km: Flight distance in kilometers

        Returns:
            Tier category: "short_haul", "medium_haul", or "long_haul"
        """
        if distance_km < CompensationService.SHORT_HAUL_THRESHOLD:
            return "short_haul"
        elif distance_km < CompensationService.MEDIUM_HAUL_THRESHOLD:
            return "medium_haul"
        else:
            return "long_haul"

    @staticmethod
    def check_extraordinary_circumstances(
        incident_description: Optional[str] = None,
        cancellation_reason: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if the incident might involve extraordinary circumstances.

        Args:
            incident_description: Description of the incident
            cancellation_reason: Reason for cancellation

        Returns:
            Tuple of (is_extraordinary, matched_keyword)
        """
        text_to_check = " ".join(filter(None, [
            incident_description or "",
            cancellation_reason or ""
        ])).lower()

        if not text_to_check:
            return False, None

        for keyword in CompensationService.EXTRAORDINARY_CIRCUMSTANCES_KEYWORDS:
            if keyword in text_to_check:
                logger.info(f"Potential extraordinary circumstances detected: {keyword}")
                return True, keyword

        return False, None

    @staticmethod
    async def calculate_compensation(
        departure_airport: str,
        arrival_airport: str,
        delay_hours: Optional[float] = None,
        incident_type: str = "delay",
        distance_km: Optional[float] = None,
        alternative_flight_offered: bool = False,
        extraordinary_circumstances: Optional[str] = None,
        use_api: bool = True
    ) -> Dict:
        """
        Calculate compensation for a flight claim.

        Args:
            departure_airport: IATA code of departure airport
            arrival_airport: IATA code of arrival airport
            delay_hours: Delay in hours (for delay incidents)
            incident_type: Type of incident (delay, cancellation, denied_boarding, baggage_delay)
            distance_km: Pre-calculated distance (optional)
            alternative_flight_offered: Whether alternative flight was offered
            extraordinary_circumstances: Known extraordinary circumstances
            use_api: Whether to use AeroDataBox API for distance calculation (default: True)

        Returns:
            Dictionary with compensation details:
            {
                "eligible": bool,
                "amount": Decimal,
                "distance_km": float,
                "reason": str,
                "requires_manual_review": bool
            }
        """
        result = {
            "eligible": False,
            "amount": Decimal("0"),
            "distance_km": 0.0,
            "reason": "",
            "requires_manual_review": False
        }

        # Calculate distance if not provided
        if distance_km is None:
            distance_km = await CompensationService.calculate_distance(
                departure_airport,
                arrival_airport,
                use_api=use_api
            )
            if distance_km is None:
                result["reason"] = "Unable to calculate distance - airport coordinates not found"
                result["requires_manual_review"] = True
                return result

        result["distance_km"] = distance_km

        # Check for extraordinary circumstances
        if extraordinary_circumstances:
            result["eligible"] = False
            result["amount"] = Decimal("0")
            result["reason"] = f"Extraordinary circumstances: {extraordinary_circumstances}"
            result["requires_manual_review"] = True
            return result

        # Get base compensation based on distance
        base_compensation = CompensationService.get_base_compensation(distance_km)

        # Handle different incident types
        if incident_type == "delay":
            if delay_hours is None:
                result["reason"] = "Delay duration not specified"
                result["requires_manual_review"] = True
                return result

            # EU261 requires 3+ hours delay for compensation
            if delay_hours < CompensationService.MIN_DELAY_FOR_COMPENSATION:
                result["eligible"] = False
                result["amount"] = Decimal("0")
                result["reason"] = f"Delay ({delay_hours:.1f}h) is less than minimum required (3h)"
                return result

            # Check for partial compensation (long haul flights with 3-4 hour delay)
            if (distance_km > CompensationService.MEDIUM_HAUL_THRESHOLD and
                CompensationService.MIN_DELAY_FOR_COMPENSATION <= delay_hours < CompensationService.PARTIAL_COMPENSATION_THRESHOLD):
                result["eligible"] = True
                result["amount"] = base_compensation * Decimal("0.2")
                result["reason"] = f"Long haul flight with 3-4 hour delay - 20% compensation"
                return result

            # Full compensation for delays >= 3 hours (or >= 4 hours for long haul)
            result["eligible"] = True
            result["amount"] = base_compensation
            result["reason"] = f"Delay of {delay_hours:.1f} hours qualifies for full compensation"

        elif incident_type == "cancellation":
            # Cancellations generally qualify for full compensation
            # unless less than 14 days notice with alternative flight
            result["eligible"] = True
            result["amount"] = base_compensation
            result["reason"] = "Flight cancellation qualifies for compensation"

            if alternative_flight_offered:
                result["requires_manual_review"] = True
                result["reason"] += " - alternative flight offered, manual review required"

        elif incident_type == "denied_boarding":
            # Denied boarding almost always qualifies for full compensation
            result["eligible"] = True
            result["amount"] = base_compensation
            result["reason"] = "Denied boarding qualifies for full compensation"

        elif incident_type == "baggage_delay":
            # Baggage delay has different compensation rules (not part of EU261)
            result["eligible"] = False
            result["amount"] = Decimal("0")
            result["reason"] = "Baggage delay compensation handled separately under Montreal Convention"
            result["requires_manual_review"] = True

        else:
            result["reason"] = f"Unknown incident type: {incident_type}"
            result["requires_manual_review"] = True

        logger.info(f"Compensation calculated: {result}")
        return result

    @staticmethod
    async def estimate_compensation_simple(
        departure_airport: str,
        arrival_airport: str,
        incident_type: str = "delay",
        use_api: bool = True
    ) -> Decimal:
        """
        Get a simple compensation estimate based on distance only.
        Useful for quick estimates before full calculation.

        Args:
            departure_airport: IATA code of departure airport
            arrival_airport: IATA code of arrival airport
            incident_type: Type of incident
            use_api: Whether to use AeroDataBox API for distance calculation (default: True)

        Returns:
            Estimated compensation amount in EUR
        """
        distance_km = await CompensationService.calculate_distance(
            departure_airport,
            arrival_airport,
            use_api=use_api
        )

        if distance_km is None:
            return Decimal("0")

        if incident_type == "baggage_delay":
            return Decimal("0")  # Not covered by EU261

        return CompensationService.get_base_compensation(distance_km)
