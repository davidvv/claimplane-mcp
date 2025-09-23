"""Claim service for business logic related to claims."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Claim, User, ClaimStatusHistory
from app.schemas import FlightDetails, PersonalInfo

logger = logging.getLogger(__name__)


class ClaimService:
    """Service for handling claim-related business logic."""
    
    def __init__(self, db: Session):
        """Initialize claim service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_claim_id(self) -> str:
        """Generate a unique claim ID.
        
        Returns:
            str: Unique claim ID
        """
        # Generate claim ID in format CL + 6 digits
        timestamp = int(datetime.utcnow().timestamp())
        return f"CL{str(timestamp)[-6:]}"
    
    def save_flight_details(self, user_id: int, flight_details: FlightDetails) -> Claim:
        """Save flight details for a claim.
        
        Args:
            user_id: User ID
            flight_details: Flight details data
            
        Returns:
            Claim: Created or updated claim
        """
        try:
            # Check if user has an existing incomplete claim
            existing_claim = self.db.query(Claim).filter(
                Claim.user_id == user_id,
                Claim.status == "submitted"
            ).first()
            
            if existing_claim:
                # Update existing claim with flight details
                existing_claim.flight_number = flight_details.flightNumber
                existing_claim.planned_departure_date = flight_details.plannedDepartureDate
                existing_claim.actual_departure_time = flight_details.actualDepartureTime
                existing_claim.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(existing_claim)
                logger.info(f"Updated flight details for claim {existing_claim.claim_id}")
                return existing_claim
            else:
                # Create new claim with flight details
                claim = Claim(
                    claim_id=self.generate_claim_id(),
                    user_id=user_id,
                    flight_number=flight_details.flightNumber,
                    planned_departure_date=flight_details.plannedDepartureDate,
                    actual_departure_time=flight_details.actualDepartureTime,
                    status="submitted"
                )
                
                self.db.add(claim)
                self.db.commit()
                self.db.refresh(claim)
                logger.info(f"Created new claim {claim.claim_id} with flight details")
                return claim
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving flight details: {e}")
            raise
    
    def save_personal_info(self, user_id: int, personal_info: PersonalInfo) -> Claim:
        """Save personal information for a claim.
        
        Args:
            user_id: User ID
            personal_info: Personal information data
            
        Returns:
            Claim: Updated claim
        """
        try:
            # Find the most recent claim for this user
            claim = self.db.query(Claim).filter(
                Claim.user_id == user_id
            ).order_by(Claim.created_at.desc()).first()
            
            if not claim:
                # Create new claim if none exists
                claim = Claim(
                    claim_id=self.generate_claim_id(),
                    user_id=user_id,
                    status="submitted"
                )
                self.db.add(claim)
            
            # Update personal information
            claim.full_name = personal_info.fullName
            claim.email = personal_info.email
            claim.booking_reference = personal_info.bookingReference
            claim.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(claim)
            logger.info(f"Updated personal info for claim {claim.claim_id}")
            return claim
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving personal info: {e}")
            raise
    
    def create_complete_claim(
        self,
        user_id: int,
        flight_details: FlightDetails,
        personal_info: PersonalInfo
    ) -> Claim:
        """Create a complete claim with all information.
        
        Args:
            user_id: User ID
            flight_details: Flight details
            personal_info: Personal information
            
        Returns:
            Claim: Created claim
        """
        try:
            # Create new claim
            claim = Claim(
                claim_id=self.generate_claim_id(),
                user_id=user_id,
                full_name=personal_info.fullName,
                email=personal_info.email,
                booking_reference=personal_info.bookingReference,
                flight_number=flight_details.flightNumber,
                planned_departure_date=flight_details.plannedDepartureDate,
                actual_departure_time=flight_details.actualDepartureTime,
                status="submitted"
            )
            
            self.db.add(claim)
            self.db.commit()
            self.db.refresh(claim)
            
            logger.info(f"Created complete claim {claim.claim_id}")
            return claim
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating complete claim: {e}")
            raise
    
    def get_claim_by_id(self, claim_id: str) -> Optional[Claim]:
        """Get claim by claim ID.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            Optional[Claim]: Claim if found, None otherwise
        """
        return self.db.query(Claim).filter(Claim.claim_id == claim_id).first()
    
    def get_claim_by_id_and_user(self, claim_id: str, user_id: int) -> Optional[Claim]:
        """Get claim by claim ID and user ID.
        
        Args:
            claim_id: Claim ID
            user_id: User ID
            
        Returns:
            Optional[Claim]: Claim if found, None otherwise
        """
        return self.db.query(Claim).filter(
            Claim.claim_id == claim_id,
            Claim.user_id == user_id
        ).first()
    
    def get_user_claims(self, user_id: int) -> List[Claim]:
        """Get all claims for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Claim]: User's claims
        """
        return self.db.query(Claim).filter(Claim.user_id == user_id).all()
    
    def get_all_claims(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Claim]:
        """Get all claims (admin function).
        
        Args:
            skip: Number of claims to skip
            limit: Maximum number of claims to return
            status_filter: Filter by status
            
        Returns:
            List[Claim]: Claims
        """
        query = self.db.query(Claim)
        
        if status_filter:
            query = query.filter(Claim.status == status_filter)
        
        return query.offset(skip).limit(limit).all()
    
    def update_claim_status(
        self,
        claim_id: str,
        new_status: str,
        changed_by: str,
        notes: Optional[str] = None
    ) -> Claim:
        """Update claim status.
        
        Args:
            claim_id: Claim ID
            new_status: New status
            changed_by: Who made the change
            notes: Optional notes
            
        Returns:
            Claim: Updated claim
        """
        try:
            claim = self.get_claim_by_id(claim_id)
            if not claim:
                raise ValueError(f"Claim {claim_id} not found")
            
            previous_status = claim.status
            claim.status = new_status
            claim.updated_at = datetime.utcnow()
            
            # Create status history entry
            status_history = ClaimStatusHistory(
                claim_id=claim.id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                notes=notes
            )
            self.db.add(status_history)
            
            self.db.commit()
            self.db.refresh(claim)
            
            logger.info(f"Updated claim {claim_id} status from {previous_status} to {new_status}")
            return claim
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating claim status: {e}")
            raise
    
    def get_claim_status_history(self, claim_id: str) -> List[ClaimStatusHistory]:
        """Get claim status history.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            List[ClaimStatusHistory]: Status history
        """
        claim = self.get_claim_by_id(claim_id)
        if not claim:
            return []
        
        return self.db.query(ClaimStatusHistory).filter(
            ClaimStatusHistory.claim_id == claim.id
        ).order_by(ClaimStatusHistory.changed_at.desc()).all()