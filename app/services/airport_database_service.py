"""
Airport Database Service

Provides fast fuzzy search for airports by IATA code, city name, or airport name.
Uses a static JSON database for instant results without external API calls.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AirportDatabaseService:
    """
    In-memory airport database with fuzzy search capabilities.

    Supports searching by:
    - IATA code (exact or prefix match)
    - City name (fuzzy match)
    - Airport name (fuzzy match)
    """

    _airports: List[Dict[str, Any]] = []
    _loaded = False

    @classmethod
    def load_database(cls) -> None:
        """Load airport database from JSON file."""
        if cls._loaded:
            return

        try:
            # Get path to airports.json
            data_dir = Path(__file__).parent.parent / "data"
            airports_file = data_dir / "airports.json"

            if not airports_file.exists():
                logger.error(f"Airport database file not found: {airports_file}")
                cls._airports = []
                cls._loaded = True
                return

            # Load JSON
            with open(airports_file, "r", encoding="utf-8") as f:
                cls._airports = json.load(f)

            logger.info(f"Loaded {len(cls._airports)} airports from database")
            cls._loaded = True

        except Exception as e:
            logger.error(f"Error loading airport database: {str(e)}", exc_info=True)
            cls._airports = []
            cls._loaded = True

    @classmethod
    def search(cls, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search airports by query.

        Supports:
        - Exact IATA code match (highest priority)
        - IATA code prefix match
        - City name fuzzy match
        - Airport name fuzzy match

        Args:
            query: Search query (IATA code, city, or airport name)
            limit: Maximum number of results

        Returns:
            List of matching airports, sorted by relevance
        """
        # Ensure database is loaded
        if not cls._loaded:
            cls.load_database()

        if not query or len(query) < 2:
            return []

        query_upper = query.upper().strip()
        query_lower = query.lower().strip()

        matches = []
        scores = []

        for airport in cls._airports:
            score = 0

            # IATA code exact match (highest priority)
            if airport["iata"].upper() == query_upper:
                score += 100

            # IATA code prefix match
            elif airport["iata"].upper().startswith(query_upper):
                score += 80

            # ICAO code match (if provided)
            if airport.get("icao") and airport["icao"].upper() == query_upper:
                score += 90
            elif airport.get("icao") and airport["icao"].upper().startswith(query_upper):
                score += 70

            # City name match
            city_lower = airport["city"].lower()
            if query_lower in city_lower:
                # Exact match
                if query_lower == city_lower:
                    score += 60
                # Starts with
                elif city_lower.startswith(query_lower):
                    score += 50
                # Contains
                else:
                    score += 30

            # Airport name match
            name_lower = airport["name"].lower()
            if query_lower in name_lower:
                # Starts with
                if name_lower.startswith(query_lower):
                    score += 40
                # Contains
                else:
                    score += 20

            # Country match (lower priority)
            country_lower = airport["country"].lower()
            if query_lower in country_lower:
                score += 10

            # If any match found, add to results
            if score > 0:
                matches.append(airport)
                scores.append(score)

        # Sort by score (descending) and take top N
        if matches:
            sorted_matches = [
                airport for _, airport in
                sorted(zip(scores, matches), key=lambda x: x[0], reverse=True)
            ]
            return sorted_matches[:limit]

        return []

    @classmethod
    def get_icao_from_iata(cls, iata_code: str) -> Optional[str]:
        """
        Convert IATA code to ICAO code.

        Args:
            iata_code: 3-letter IATA code (e.g., "MUC", "JFK")

        Returns:
            4-letter ICAO code (e.g., "EDDM", "KJFK") or None if not found
        """
        # Ensure database is loaded
        if not cls._loaded:
            cls.load_database()

        if not iata_code or len(iata_code) != 3:
            return None

        iata_upper = iata_code.upper().strip()

        # Search for exact IATA match
        for airport in cls._airports:
            if airport["iata"].upper() == iata_upper:
                return airport.get("icao")

        return None


# Auto-load on module import
AirportDatabaseService.load_database()
