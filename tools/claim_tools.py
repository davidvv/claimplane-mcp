"""Claim management tools."""
from typing import Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy import select
from database import get_db_session
from app.models import Claim, ClaimNote, ClaimStatusHistory
from app.repositories import ClaimRepository
from app.services.compensation_service import CompensationService
from app.services.claim_workflow_service import ClaimWorkflowService


async def create_claim(
    customer_id: str,
    flight_number: str,
    flight_date: str,
    departure_airport: str,
    arrival_airport: str,
    incident_type: str,
    scheduled_departure: Optional[str] = None,
    actual_departure: Optional[str] = None,
    scheduled_arrival: Optional[str] = None,
    actual_arrival: Optional[str] = None,
    delay_minutes: Optional[int] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new claim.
    
    Args:
        customer_id: Customer ID (UUID)
        flight_number: Flight number (e.g., "LH123")
        flight_date: Flight date (YYYY-MM-DD)
        departure_airport: Departure airport IATA code
        arrival_airport: Arrival airport IATA code
        incident_type: Type of incident (delay, cancellation, denied_boarding, missed_connection)
        scheduled_departure: Scheduled departure time (ISO format, optional)
        actual_departure: Actual departure time (ISO format, optional)
        scheduled_arrival: Scheduled arrival time (ISO format, optional)
        actual_arrival: Actual arrival time (ISO format, optional)
        delay_minutes: Delay in minutes (optional)
        description: Claim description (optional)
    
    Returns:
        Created claim details with compensation calculation
    """
    try:
        async with get_db_session() as session:
            repo = ClaimRepository(session)
            
            # Parse flight date
            flight_date_obj = datetime.strptime(flight_date, "%Y-%m-%d").date()
            
            # Infer airline from flight number
            airline = "Unknown"
            if len(flight_number) >= 2:
                airline = flight_number[:2]
            
            # Create claim
            claim = await repo.create(
                customer_id=customer_id,
                flight_number=flight_number,
                airline=airline,
                departure_date=flight_date_obj,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                incident_type=incident_type,
                delay_hours=round(delay_minutes / 60, 2) if delay_minutes else None,
                notes=description,
                status="submitted"
            )
            
            # Calculate compensation if enough data
            compensation_amount = None
            if delay_minutes and departure_airport and arrival_airport:
                try:
                    comp_service = CompensationService()
                    compensation_amount = await comp_service.calculate_compensation(
                        departure_iata=departure_airport,
                        arrival_iata=arrival_airport,
                        delay_minutes=delay_minutes,
                        incident_type=incident_type
                    )
                    
                    # Update claim with compensation
                    claim.compensation_amount = compensation_amount
                    await session.commit()
                except Exception as comp_error:
                    # Compensation calculation failed but claim created
                    pass
            
            return {
                "success": True,
                "claim_id": str(claim.id),
                "status": claim.status,
                "flight_number": claim.flight_number,
                "flight_date": claim.departure_date.isoformat(),
                "incident_type": claim.incident_type,
                "compensation_amount": compensation_amount,
                "message": f"Claim created successfully: {claim.id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create claim"
        }


async def get_claim(claim_id: str) -> Dict[str, Any]:
    """Get claim by ID with full details.
    
    Args:
        claim_id: Claim ID (UUID)
    
    Returns:
        Complete claim details
    """
    try:
        async with get_db_session() as session:
            repo = ClaimRepository(session)
            claim = await repo.get_by_id(claim_id)
            
            if not claim:
                return {
                    "success": False,
                    "message": f"Claim not found: {claim_id}"
                }
            
            return {
                "success": True,
                "claim": {
                    "id": str(claim.id),
                    "customer_id": str(claim.customer_id),
                    "flight_number": claim.flight_number,
                    "flight_date": claim.departure_date.isoformat() if claim.departure_date else None,
                    "departure_airport": claim.departure_airport,
                    "arrival_airport": claim.arrival_airport,
                    "incident_type": claim.incident_type,
                    "status": claim.status,
                    "delay_minutes": int(claim.delay_hours * 60) if claim.delay_hours else None,
                    "compensation_amount": float(claim.compensation_amount) if claim.compensation_amount else None,
                    "description": claim.notes,
                    "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
                    "updated_at": claim.updated_at.isoformat() if claim.updated_at else None
                },
                "message": "Claim retrieved successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve claim"
        }


async def list_claims(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """List claims with optional filters.
    
    Args:
        customer_id: Filter by customer ID (optional)
        status: Filter by status (optional)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    
    Returns:
        List of claims
    """
    try:
        async with get_db_session() as session:
            query = select(Claim).order_by(Claim.submitted_at.desc())
            
            if customer_id:
                query = query.where(Claim.customer_id == customer_id)
            if status:
                query = query.where(Claim.status == status)
            
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            claims = result.scalars().all()
            
            return {
                "success": True,
                "count": len(claims),
                "claims": [
                    {
                        "id": str(c.id),
                        "customer_id": str(c.customer_id),
                        "flight_number": c.flight_number,
                        "flight_date": c.departure_date.isoformat() if c.departure_date else None,
                        "status": c.status,
                        "compensation_amount": float(c.compensation_amount) if c.compensation_amount else None,
                        "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None
                    }
                    for c in claims
                ],
                "message": f"Retrieved {len(claims)} claims"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list claims"
        }


async def transition_claim_status(
    claim_id: str,
    new_status: str,
    admin_id: Optional[str] = None,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """Transition claim to a new status.
    
    Args:
        claim_id: Claim ID (UUID)
        new_status: New status (submitted, under_review, approved, rejected, paid)
        admin_id: Admin user ID performing transition (optional)
        note: Note about the transition (optional)
    
    Returns:
        Updated claim status
    """
    try:
        async with get_db_session() as session:
            repo = ClaimRepository(session)
            claim = await repo.get_by_id(claim_id)
            
            if not claim:
                return {
                    "success": False,
                    "message": f"Claim not found: {claim_id}"
                }
            
            old_status = claim.status
            
            # Update status
            claim.status = new_status
            
            # Create status history entry
            if ClaimStatusHistory:
                history = ClaimStatusHistory(
                    claim_id=claim.id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=admin_id,
                    notes=note
                )
                session.add(history)
            
            await session.commit()
            
            return {
                "success": True,
                "claim_id": str(claim.id),
                "old_status": old_status,
                "new_status": new_status,
                "message": f"Claim status updated from {old_status} to {new_status}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update claim status"
        }


async def add_claim_note(
    claim_id: str,
    note: str,
    admin_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a note to a claim.
    
    Args:
        claim_id: Claim ID (UUID)
        note: Note content
        admin_id: Admin user ID (optional)
    
    Returns:
        Note creation status
    """
    try:
        async with get_db_session() as session:
            repo = ClaimRepository(session)
            claim = await repo.get_by_id(claim_id)
            
            if not claim:
                return {
                    "success": False,
                    "message": f"Claim not found: {claim_id}"
                }
            
            # Create note
            claim_note = ClaimNote(
                claim_id=claim.id,
                note=note,
                created_by=admin_id
            )
            session.add(claim_note)
            await session.commit()
            
            return {
                "success": True,
                "note_id": str(claim_note.id),
                "claim_id": str(claim.id),
                "message": "Note added successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add note"
        }
