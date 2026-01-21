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
            
            # --- 1. Clean up Template (Blank out placeholders and boxes) ---
            
            # A. Identify and blank out the large signature box (Drawing [2] from inspection)
            # It's at Rect(72.0, 762.8, 523.3, 849.2). This is the "red/gray box".
            signature_box_rect = fitz.Rect(72, 760, 525, 850)
            page.draw_rect(signature_box_rect, color=(1, 1, 1), fill=(1, 1, 1))

            # B. Blank out specific UI text placeholders
            ui_placeholders = ["[Electronic Signature Will Be Placed Here]", "{{audit_trail_id}}"]
            for ui_p in ui_placeholders:
                hits = page.search_for(ui_p)
                for rect in hits:
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # --- 2. Data Preparation ---
            
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
            }

            # --- 3. Text Replacements ---
            for placeholder, value in replacements.items():
                hits = page.search_for(placeholder)
                if not hits:
                    logger.warning(f"Placeholder not found in POA template: {placeholder}")
                for rect in hits:
                    # Draw small white box just over the placeholder text to erase it
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    # Insert new text
                    # Use y1 - 2 to place text baseline correctly. 
                    # Ensure color is black.
                    page.insert_text((rect.x0, rect.y1 - 2), str(value), fontsize=10, fontname="helv", color=(0, 0, 0))
            
            # --- 4. Signature Overlay ---
            if signature_image_bytes and len(signature_image_bytes) > 100:
                logger.info(f"Inserting signature image: {len(signature_image_bytes)} bytes")
                # Position it in the cleared signature area, slightly higher to not hit audit trail
                SIGNATURE_BOX = fitz.Rect(100, 765, 500, 825)
                page.insert_image(SIGNATURE_BOX, stream=signature_image_bytes)
            else:
                logger.warning(f"Signature image too small or missing ({len(signature_image_bytes) if signature_image_bytes else 0} bytes)")
            
            # --- 5. Audit Trail ---
            audit_text = (
                f"Digitally signed by: {signer_name} | IP: {ip_address} | "
                f"Date: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | "
                f"Device: {user_agent[:40]}..."
            )
            
            # Place audit trail at the absolute bottom
            page.insert_text(
                (86, 835), 
                audit_text,
                fontsize=7,
                color=(0.3, 0.3, 0.3)
            )

            # Return bytes
            return doc.tobytes()
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}", exc_info=True)
            raise
