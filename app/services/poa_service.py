"""Service for generating signed Power of Attorney PDFs."""
import os
import io
import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class POAService:
    """Service for generating signed Power of Attorney PDFs."""
    
    TEMPLATE_PATH = "app/templates/legal/poa_template.pdf"
    
    # Signature placement coordinates (Page 1)
    # Based on A4 (595 x 842)
    # Moved to clear the passenger/address section (y=636-693)
    # Placed between SIGNATURE header (y=728) and footer (y=796)
    SIGNATURE_RECT = fitz.Rect(86, 735, 510, 790) 
    
    @staticmethod
    def generate_signed_poa(
        flight_number: str,
        flight_date: str,
        departure_airport: str,
        arrival_airport: str,
        booking_reference: str,
        primary_passenger_name: str,
        additional_passengers: str,
        address: str,
        signer_name: str,
        signature_image_bytes: bytes,
        ip_address: str,
        user_agent: str,
        signed_at: datetime
    ) -> bytes:
        """
        Generate a signed POA PDF.
        """
        try:
            # Load template
            if not os.path.exists(POAService.TEMPLATE_PATH):
                raise FileNotFoundError(f"POA template not found at {POAService.TEMPLATE_PATH}")
                
            doc = fitz.open(POAService.TEMPLATE_PATH)
            page = doc[0]  # Assuming single page
            
            # --- Text Replacements ---
            # Clean up passenger names: filter out "None" or junk from OCR
            if additional_passengers:
                # Remove common OCR/Backend artifacts
                additional_passengers = additional_passengers.replace("None", "").strip(", \n\t")
                if not additional_passengers:
                    additional_passengers = "None"
            else:
                additional_passengers = "None"

            replacements = {
                "{{flight_number}}": flight_number or "-",
                "{{flight_date}}": flight_date or "-",
                "{{departure_airport}}": departure_airport or "-",
                "{{arrival_airport}}": arrival_airport or "-",
                "{{booking_reference}}": booking_reference or "-",
                "{{primary_passenger_name}}": primary_passenger_name or "-",
                "{{additional_passengers}}": additional_passengers,
                "{{address}}": address or "-",
                "{{signer_name}}": signer_name,
                "{{signed_date}}": signed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
            # 1. Replace data placeholders
            for placeholder, value in replacements.items():
                hits = page.search_for(placeholder)
                for rect in hits:
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text((rect.x0, rect.y1 - 2), str(value), fontsize=10, fontname="Helvetica")
            
            # 2. Clean up specific UI placeholders to prevent "underlay" look
            ui_placeholders = ["[Electronic Signature Will Be Placed Here]", "{{audit_trail_id}}"]
            for ui_p in ui_placeholders:
                hits = page.search_for(ui_p)
                for rect in hits:
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # 3. Aggressively remove any large rectangles/boxes in the signature area
            # The template has gray/red boxes that we want to clear
            drawings = page.get_drawings()
            for d in drawings:
                r = d["rect"]
                # If it's a wide box in the bottom half of the page, cover it
                if r.width > 300 and r.y0 > 450:
                    page.draw_rect(r, color=(1, 1, 1), fill=(1, 1, 1))

            # --- Signature Overlay ---
            # Center the signature in the area formerly occupied by the bottom box (y ~ 762-840)
            # We'll place it slightly above the audit trail
            SIGNATURE_BOX = fitz.Rect(86, 755, 510, 805)
            page.insert_image(SIGNATURE_BOX, stream=signature_image_bytes)
            
            # --- Audit Trail ---
            audit_text = (
                f"Digitally signed by: {signer_name} | IP: {ip_address} | "
                f"Date: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | "
                f"Device: {user_agent[:40]}..."
            )
            
            # Place audit trail at the very bottom
            page.insert_text(
                (86, 825), 
                audit_text,
                fontsize=7,
                color=(0.4, 0.4, 0.4)
            )
            
            # Return bytes
            return doc.tobytes()
            
            # Return bytes
            return doc.tobytes()
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}")
            raise

