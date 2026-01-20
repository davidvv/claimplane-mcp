"""Service for verifying claim completeness and document requirements."""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models import Claim, ClaimFile, Customer

logger = logging.getLogger(__name__)

class ClaimVerificationService:
    """Service to determine if a claim has sufficient data and documents."""

    @staticmethod
    def verify_claim(claim: Claim, customer: Customer, files: List[ClaimFile]) -> Dict[str, Any]:
        """
        Check if the claim is complete or needs more data/documents.
        
        Logic based on industry research:
        - If PNR (Booking Reference) is provided, boarding pass is NOT strictly mandatory for airlines.
        - As an agency, Power of Attorney (POA) IS mandatory.
        - If PNR is missing, Boarding Pass or Ticket becomes mandatory.
        """
        missing_data = []
        missing_documents = []
        
        # 1. Essential Customer Data
        if not customer.first_name or not customer.last_name:
            missing_data.append("full_name")
        if not customer.email:
            missing_data.append("email")
        if not customer.street or not customer.city or not customer.country:
            missing_data.append("address")
            
        # 2. Essential Flight Data
        if not claim.flight_number:
            missing_data.append("flight_number")
        if not claim.departure_date:
            missing_data.append("departure_date")
        if not claim.departure_airport or not claim.arrival_airport:
            missing_data.append("airports")
            
        # 3. Document/Evidence Logic
        has_pnr = bool(claim.booking_reference)
        has_boarding_pass = any(f.document_type == ClaimFile.DOCUMENT_BOARDING_PASS for f in files)
        has_ticket = any(f.document_type == ClaimFile.DOCUMENT_FLIGHT_TICKET for f in files)
        has_poa = any(f.document_type == ClaimFile.DOCUMENT_POWER_OF_ATTORNEY for f in files)
        
        # Power of Attorney is always required for legal representation
        if not has_poa:
            missing_documents.append(ClaimFile.DOCUMENT_POWER_OF_ATTORNEY)
            
        # If no PNR, we need a boarding pass or ticket as proof of presence
        if not has_pnr and not has_boarding_pass and not has_ticket:
            missing_documents.append(ClaimFile.DOCUMENT_BOARDING_PASS)
            
        # Determine if we can skip the "at least one document" requirement
        # (Assuming the "at least one document" was a generic rule)
        can_submit_without_more_uploads = has_poa and (has_pnr or has_boarding_pass or has_ticket)
        
        is_complete = len(missing_data) == 0 and len(missing_documents) == 0
        
        return {
            "is_complete": is_complete,
            "missing_data": missing_data,
            "missing_documents": missing_documents,
            "has_pnr": has_pnr,
            "has_poa": has_poa,
            "poa_signed": has_poa,
            "can_submit": can_submit_without_more_uploads,
            "recommendation": "Ready for submission" if is_complete else "Needs more information"
        }
