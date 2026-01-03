"""Airport taxi time lookup service for accurate EU261 delay calculations."""
import csv
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AirportTaxiTimeService:
    """
    Service for looking up airport-specific taxi times.

    EU261/2004 regulations measure delay based on gate arrival (door opening),
    not runway touchdown. Since AeroDataBox only provides runway times, we add
    airport-specific taxi-in times to convert runway touchdown to gate arrival.

    Data source: docs/comprehensive_airport_taxiing_times.csv (184 airports)
    """

    # Class-level cache of airport taxi times
    _taxi_times: Dict[str, Dict[str, float]] = {}
    _loaded: bool = False

    @classmethod
    def load_taxi_times(cls, csv_path: str = "docs/comprehensive_airport_taxiing_times.csv") -> None:
        """
        Load taxi times from CSV file into memory.

        Args:
            csv_path: Path to CSV file with airport taxi times

        CSV Format:
            Region,IATA,City,Airport Name,Taxi-Out (min),Taxi-In (min)

        Example:
            Europe,FRA,Frankfurt,Frankfurt,13.2,5.3
            United States,IAD,Washington,Washington Dulles,21.5,10.7

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV has invalid format
        """
        if cls._loaded:
            logger.info("Airport taxi times already loaded")
            return

        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Airport taxi times CSV not found: {csv_path}")

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Verify required columns
                required_columns = {'IATA', 'Taxi-Out (min)', 'Taxi-In (min)'}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    raise ValueError(
                        f"CSV missing required columns. Expected: {required_columns}, "
                        f"Found: {reader.fieldnames}"
                    )

                airports_loaded = 0
                for row in reader:
                    iata = row.get('IATA', '').strip().upper()
                    if not iata:
                        continue

                    try:
                        taxi_out = float(row.get('Taxi-Out (min)', 0))
                        taxi_in = float(row.get('Taxi-In (min)', 0))

                        cls._taxi_times[iata] = {
                            'taxi_out': taxi_out,
                            'taxi_in': taxi_in,
                            'region': row.get('Region', '').strip(),
                            'city': row.get('City', '').strip(),
                            'airport_name': row.get('Airport Name', '').strip()
                        }
                        airports_loaded += 1

                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Skipping invalid taxi time data for {iata}: {e}"
                        )
                        continue

            cls._loaded = True
            logger.info(
                f"Successfully loaded taxi times for {airports_loaded} airports from {csv_path}"
            )

        except Exception as e:
            logger.error(f"Failed to load airport taxi times: {e}", exc_info=True)
            raise

    @classmethod
    def get_taxi_in_time(cls, airport_iata: str, default: float = 15.0) -> float:
        """
        Get taxi-in time for arrival airport.

        Taxi-in is the time from runway touchdown to gate arrival (door opening).
        This is what we need to add to runway arrival time to get gate arrival time
        for accurate EU261 delay calculations.

        Args:
            airport_iata: 3-letter IATA airport code (e.g., 'JFK', 'LHR')
            default: Default taxi-in time if airport not found (minutes)

        Returns:
            Taxi-in time in minutes (float)

        Examples:
            >>> get_taxi_in_time('JFK')
            13.3  # JFK taxi-in time from CSV
            >>> get_taxi_in_time('UNKNOWN')
            15.0  # Default fallback
        """
        if not cls._loaded:
            logger.warning("Airport taxi times not loaded. Using default.")
            return default

        iata = airport_iata.upper().strip()
        airport_data = cls._taxi_times.get(iata)

        if not airport_data:
            logger.debug(
                f"No taxi time data for {iata}. Using default {default} min."
            )
            return default

        taxi_in = airport_data.get('taxi_in', default)
        logger.debug(
            f"Taxi-in time for {iata} ({airport_data.get('airport_name')}): {taxi_in} min"
        )
        return taxi_in

    @classmethod
    def get_taxi_out_time(cls, airport_iata: str, default: float = 15.0) -> float:
        """
        Get taxi-out time for departure airport.

        Taxi-out is the time from gate departure to wheels-up (runway departure).

        NOTE: Based on AeroDataBox API testing, departure times appear to already
        be gate times, so taxi-out adjustments are NOT currently needed. This method
        is provided for completeness and potential future use.

        Args:
            airport_iata: 3-letter IATA airport code (e.g., 'JFK', 'LHR')
            default: Default taxi-out time if airport not found (minutes)

        Returns:
            Taxi-out time in minutes (float)
        """
        if not cls._loaded:
            logger.warning("Airport taxi times not loaded. Using default.")
            return default

        iata = airport_iata.upper().strip()
        airport_data = cls._taxi_times.get(iata)

        if not airport_data:
            logger.debug(
                f"No taxi time data for {iata}. Using default {default} min."
            )
            return default

        taxi_out = airport_data.get('taxi_out', default)
        logger.debug(
            f"Taxi-out time for {iata} ({airport_data.get('airport_name')}): {taxi_out} min"
        )
        return taxi_out

    @classmethod
    def get_airport_info(cls, airport_iata: str) -> Optional[Dict[str, any]]:
        """
        Get complete airport information including taxi times.

        Args:
            airport_iata: 3-letter IATA airport code

        Returns:
            Dictionary with airport data or None if not found

        Example:
            {
                'taxi_out': 13.2,
                'taxi_in': 5.3,
                'region': 'Europe',
                'city': 'Frankfurt',
                'airport_name': 'Frankfurt'
            }
        """
        if not cls._loaded:
            return None

        iata = airport_iata.upper().strip()
        return cls._taxi_times.get(iata)

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if taxi times have been loaded."""
        return cls._loaded

    @classmethod
    def get_airport_count(cls) -> int:
        """Get number of airports with taxi time data."""
        return len(cls._taxi_times)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the loaded taxi times cache (useful for testing)."""
        cls._taxi_times.clear()
        cls._loaded = False
        logger.info("Airport taxi times cache cleared")
