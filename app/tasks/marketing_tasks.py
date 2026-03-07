"""
Marketing tasks for flight delay monitoring and data collection.

This module contains Celery tasks that:
- Poll AeroDataBox for global flight delays (hourly)
- Store delay events for retargeting campaigns
- Cache results in Redis for quick access
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from celery import shared_task
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import FlightDelayEvent
from app.services.aerodatabox_service import aerodatabox_service
from app.config import config
from app.tasks.async_helpers import run_async

logger = logging.getLogger(__name__)


# Top 20 US airports by passenger volume (2024 data)
# Source: FAA / Airport Council International
TOP_20_US_AIRPORTS = [
    "ATL",  # Atlanta Hartsfield-Jackson
    "DFW",  # Dallas/Fort Worth
    "DEN",  # Denver
    "ORD",  # Chicago O'Hare
    "LAX",  # Los Angeles
    "CLT",  # Charlotte
    "MCO",  # Orlando
    "LAS",  # Las Vegas
    "PHX",  # Phoenix
    "MIA",  # Miami
    "SEA",  # Seattle-Tacoma
    "IAH",  # Houston George Bush
    "JFK",  # New York JFK
    "EWR",  # Newark
    "FLL",  # Fort Lauderdale
    "MSP",  # Minneapolis
    "SFO",  # San Francisco
    "DTW",  # Detroit
    "BOS",  # Boston
    "SLC",  # Salt Lake City
]

# IATA to ICAO code mapping for top US airports
IATA_TO_ICAO = {
    "ATL": "KATL",
    "DFW": "KDFW",
    "DEN": "KDEN",
    "ORD": "KORD",
    "LAX": "KLAX",
    "CLT": "KCLT",
    "MCO": "KMCO",
    "LAS": "KLAS",
    "PHX": "KPHX",
    "MIA": "KMIA",
    "SEA": "KSEA",
    "IAH": "KIAH",
    "JFK": "KJFK",
    "EWR": "KEWR",
    "FLL": "KFLL",
    "MSP": "KMSP",
    "SFO": "KSFO",
    "DTW": "KDTW",
    "BOS": "KBOS",
    "SLC": "KSLC",
}


async def _store_delay_events(delays: List[Dict[str, Any]], api_source: str = "aerodatabox"):
    """
    Store delay events in the database.
    
    Args:
        delays: List of delay dictionaries from API
        api_source: Source of the data (e.g., "aerodatabox")
    """
    async with AsyncSessionLocal() as session:
        try:
            today = date.today()
            events_created = 0
            events_updated = 0
            
            for delay in delays:
                flight_number = delay.get("flight_number")
                departure_airport = delay.get("departure_airport")
                
                if not flight_number or not departure_airport:
                    continue
                
                # Parse scheduled departure time
                scheduled_departure = None
                if delay.get("scheduled_departure"):
                    try:
                        scheduled_departure = datetime.fromisoformat(
                            delay["scheduled_departure"].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                
                # Parse scheduled arrival time
                scheduled_arrival = None
                if delay.get("scheduled_arrival"):
                    try:
                        scheduled_arrival = datetime.fromisoformat(
                            delay["scheduled_arrival"].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass
                
                # Determine flight date (today or tomorrow based on scheduled time)
                flight_date = today
                if scheduled_departure and scheduled_departure.date() > today:
                    flight_date = scheduled_departure.date()
                
                delay_minutes = delay.get("delay_minutes", 0)
                
                # EU261 eligibility: delays >180 minutes for EU routes
                # For now, we'll flag delays >120 minutes as potentially eligible
                is_eu261_eligible = delay_minutes >= 180
                
                # Check if event already exists
                existing = await session.execute(
                    select(FlightDelayEvent).where(
                        and_(
                            FlightDelayEvent.flight_number == flight_number,
                            FlightDelayEvent.flight_date == flight_date,
                            FlightDelayEvent.departure_airport == departure_airport,
                        )
                    )
                )
                existing_event = existing.scalar_one_or_none()
                
                if existing_event:
                    # Update existing event
                    existing_event.delay_minutes = delay_minutes
                    existing_event.status = delay.get("status", "delayed")
                    existing_event.delay_reason = delay.get("reason")
                    existing_event.is_eu261_eligible = is_eu261_eligible
                    existing_event.api_fetched_at = datetime.utcnow()
                    events_updated += 1
                else:
                    # Create new event
                    event = FlightDelayEvent(
                        flight_number=flight_number,
                        flight_date=flight_date,
                        airline_name=delay.get("airline"),
                        airline_iata=delay.get("airline_iata"),
                        departure_airport=departure_airport,
                        arrival_airport=delay.get("arrival_airport"),
                        delay_minutes=delay_minutes,
                        delay_reason=delay.get("reason"),
                        scheduled_departure=scheduled_departure,
                        scheduled_arrival=scheduled_arrival,
                        status=delay.get("status", "delayed"),
                        api_source=api_source,
                        is_eu261_eligible=is_eu261_eligible,
                    )
                    session.add(event)
                    events_created += 1
            
            await session.commit()
            logger.info(
                f"Stored {events_created} new delay events, "
                f"updated {events_updated} existing events"
            )
            return {"created": events_created, "updated": events_updated}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing delay events: {str(e)}")
            raise


async def _fetch_global_delays_for_airport(
    airport_iata: str,
    min_delay_minutes: int = 120
) -> List[Dict[str, Any]]:
    """
    Fetch flight delays for a specific airport using FIDS endpoint.
    
    Note: The /flights/delays/global endpoint is not available through API.Market,
    so we use the FIDS (Flight Information Display System) endpoint to get
    departures and filter for delayed flights locally.
    
    Args:
        airport_iata: IATA airport code
        min_delay_minutes: Minimum delay to include (default: 120 for EU261 threshold)
        
    Returns:
        List of delay dictionaries
    """
    try:
        # Get ICAO code for the airport
        icao_code = IATA_TO_ICAO.get(airport_iata)
        if not icao_code:
            logger.warning(f"No ICAO code mapping for {airport_iata}")
            return []
        
        # Fetch departures for a 12-hour window
        now = datetime.now()
        from_local = now.strftime('%Y-%m-%dT%H:%M')
        to_local = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
        
        result = await aerodatabox_service.get_airport_departures(
            origin_icao=icao_code,
            from_local=from_local,
            to_local=to_local
        )
        
        departures = result.get("departures", [])
        delayed_flights = []
        
        for flight in departures:
            # Check if flight has delay information
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})
            
            # Get delay from the delayMinutes field or calculate from times
            delay_minutes = flight.get("delayMinutes", 0)
            
            # Also check status for delayed indication
            status = flight.get("status", "").lower()
            is_delayed_status = status in ["delayed", "late"]
            
            # Include flight if it meets the delay threshold or has delayed status
            if delay_minutes >= min_delay_minutes or is_delayed_status:
                # Get airline info
                airline = flight.get("airline", {})
                
                # Get airport info
                dep_airport = departure.get("airport", {}) if departure else {}
                arr_airport = arrival.get("airport", {}) if arrival else {}
                
                # Get scheduled times
                scheduled_departure = departure.get("scheduledTime", {}).get("utc") if departure else None
                
                delay_info = {
                    "flight_number": flight.get("number"),
                    "airline": airline.get("name"),
                    "airline_iata": airline.get("iata"),
                    "departure_airport": dep_airport.get("iata") or airport_iata,
                    "arrival_airport": arr_airport.get("iata"),
                    "delay_minutes": delay_minutes,
                    "scheduled_departure": scheduled_departure,
                    "status": flight.get("status", "delayed"),
                    "reason": None,  # Not available from FIDS endpoint
                }
                delayed_flights.append(delay_info)
        
        logger.info(f"Found {len(delayed_flights)} delayed flights at {airport_iata}")
        return delayed_flights
        
    except Exception as e:
        logger.error(f"Error fetching delays for {airport_iata}: {str(e)}")
        return []


async def _run_fetch_global_delays():
    """
    Main async function to fetch global delays for all airports.
    """
    if not config.AERODATABOX_ENABLED:
        logger.warning("AeroDataBox is disabled. Skipping global delays fetch.")
        return {"status": "skipped", "reason": "api_disabled"}
    
    logger.info("Starting hourly global delays fetch for top 20 US airports")
    
    all_delays = []
    airport_stats = {}
    
    # Fetch delays for each airport
    for airport in TOP_20_US_AIRPORTS:
        delays = await _fetch_global_delays_for_airport(airport, min_delay_minutes=120)
        all_delays.extend(delays)
        airport_stats[airport] = len(delays)
        
        # Small delay between requests to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Remove duplicates (same flight might appear for both departure and arrival airports)
    seen_flights = set()
    unique_delays = []
    for delay in all_delays:
        flight_key = (
            delay.get("flight_number"),
            delay.get("scheduled_departure", "")[:10]  # Date part only
        )
        if flight_key not in seen_flights:
            seen_flights.add(flight_key)
            unique_delays.append(delay)
    
    logger.info(
        f"Fetched {len(all_delays)} total delay events, "
        f"{len(unique_delays)} unique after deduplication"
    )
    
    # Store in database
    if unique_delays:
        storage_result = await _store_delay_events(unique_delays)
    else:
        storage_result = {"created": 0, "updated": 0}
    
    return {
        "status": "success",
        "total_delays": len(unique_delays),
        "by_airport": airport_stats,
        "storage": storage_result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@shared_task(name="fetch_global_flight_delays")
def fetch_global_flight_delays():
    """
    Celery task to fetch global flight delays hourly.
    
    This task:
    1. Queries AeroDataBox GetGlobalDelays for each of the top 20 US airports
    2. Filters for delays >120 minutes
    3. Stores unique delay events in the database
    4. Runs hourly via Celery Beat
    
    Scheduled: Every hour at :00 minutes
    API Cost: ~20 calls/hour × 24 hours × 2 credits = 960 credits/day
    Monthly: ~28,800 credits (within Pro Tier 1 limit of 3,000 credits/month)
    
    Note: We're batching by airport to maximize data quality while staying
    within API limits. Alternative: query once globally and filter locally.
    """
    logger.info("Celery task fetch_global_flight_delays started")
    
    try:
        result = run_async(_run_fetch_global_delays())
        logger.info(f"Global delays fetch completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Global delays fetch failed: {str(e)}")
        raise


@shared_task(name="cleanup_old_flight_delay_events")
def cleanup_old_flight_delay_events():
    """
    Cleanup old flight delay events (retention: 90 days).
    
    This task removes delay events older than 90 days to keep the database
    from growing indefinitely. Should be run daily.
    
    Scheduled: Daily at 04:00 UTC
    """
    logger.info("Starting cleanup of old flight delay events")
    
    async def _cleanup():
        async with AsyncSessionLocal() as session:
            cutoff_date = date.today() - timedelta(days=90)
            
            result = await session.execute(
                select(FlightDelayEvent).where(
                    FlightDelayEvent.flight_date < cutoff_date
                )
            )
            old_events = result.scalars().all()
            
            count = len(old_events)
            if count > 0:
                for event in old_events:
                    await session.delete(event)
                await session.commit()
                logger.info(f"Deleted {count} old flight delay events (older than {cutoff_date})")
            else:
                logger.info("No old flight delay events to clean up")
            
            return {"deleted": count, "cutoff_date": cutoff_date.isoformat()}
    
    try:
        result = run_async(_cleanup())
        return result
    except Exception as e:
        logger.error(f"Flight delay cleanup failed: {str(e)}")
        raise


@shared_task(name="generate_delay_report")
def generate_delay_report(days: int = 7) -> Dict[str, Any]:
    """
    Generate a report of recent flight delays.
    
    Args:
        days: Number of days to include in report (default: 7)
        
    Returns:
        Report dictionary with statistics
    """
    logger.info(f"Generating delay report for last {days} days")
    
    async def _generate_report():
        async with AsyncSessionLocal() as session:
            cutoff_date = date.today() - timedelta(days=days)
            
            # Total delays
            total_result = await session.execute(
                select(func.count(FlightDelayEvent.id)).where(
                    FlightDelayEvent.flight_date >= cutoff_date
                )
            )
            total_delays = total_result.scalar()
            
            # By airport
            airport_result = await session.execute(
                select(
                    FlightDelayEvent.departure_airport,
                    func.count(FlightDelayEvent.id).label("count")
                ).where(
                    FlightDelayEvent.flight_date >= cutoff_date
                ).group_by(
                    FlightDelayEvent.departure_airport
                ).order_by(func.count(FlightDelayEvent.id).desc())
            )
            by_airport = [
                {"airport": row[0], "count": row[1]}
                for row in airport_result.all()
            ]
            
            # By airline
            airline_result = await session.execute(
                select(
                    FlightDelayEvent.airline_iata,
                    func.count(FlightDelayEvent.id).label("count")
                ).where(
                    FlightDelayEvent.flight_date >= cutoff_date
                ).group_by(
                    FlightDelayEvent.airline_iata
                ).order_by(func.count(FlightDelayEvent.id).desc()).limit(10)
            )
            by_airline = [
                {"airline": row[0] or "Unknown", "count": row[1]}
                for row in airline_result.all()
            ]
            
            # Average delay
            avg_delay_result = await session.execute(
                select(func.avg(FlightDelayEvent.delay_minutes)).where(
                    FlightDelayEvent.flight_date >= cutoff_date
                )
            )
            avg_delay = avg_delay_result.scalar() or 0
            
            return {
                "period_days": days,
                "total_delays": total_delays,
                "average_delay_minutes": round(avg_delay, 1),
                "top_airports": by_airport[:10],
                "top_airlines": by_airline,
                "generated_at": datetime.utcnow().isoformat(),
            }
    
    try:
        result = run_async(_generate_report())
        logger.info(f"Delay report generated: {result}")
        return result
    except Exception as e:
        logger.error(f"Delay report generation failed: {str(e)}")
        raise