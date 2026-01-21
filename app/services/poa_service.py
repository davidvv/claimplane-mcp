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
            
            # 1. Clean up Template (Blank out placeholders and boxes)
            
            # A. Identify and blank out the large signature box (Drawing [2] from inspection)
            # It's at Rect(72.0, 762.8, 523.3, 849.2). 
            signature_box_rect = fitz.Rect(70, 750, 530, 850)
            page.draw_rect(signature_box_rect, color=(1, 1, 1), fill=(1, 1, 1))

            # B. Blank out specific UI text placeholders
            ui_placeholders = ["[Electronic Signature Will Be Placed Here]", "{{audit_trail_id}}"]
            for ui_p in ui_placeholders:
                hits = page.search_for(ui_p)
                for rect in hits:
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # C. Look for any red-ish drawings and cover them
            drawings = page.get_drawings()
            for d in drawings:
                c = d.get("color") or d.get("fill")
                if c and c[0] > 0.6 and c[1] < 0.4 and c[2] < 0.4:
                    logger.info(f"Covering red drawing at {d['rect']}")
                    page.draw_rect(d["rect"], color=(1, 1, 1), fill=(1, 1, 1))

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
                    continue
                    
                for rect in hits:
                    # Erase placeholder with a slightly larger white box to be safe
                    # Rect is (x0, y0, x1, y1)
                    erase_rect = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
                    page.draw_rect(erase_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # Insert value
                    # Using Helvetica for maximum compatibility.
                    # PyMuPDF's insert_text uses (x, y) as the baseline start.
                    # rect.y1 is the bottom of the bounding box.
                    text_pos = fitz.Point(rect.x0, rect.y1 - 2)
                    
                    val_str = str(value)
                    fontsize = 10
                    if len(val_str) > 40:
                        fontsize = 7
                    elif len(val_str) > 25:
                        fontsize = 8
                    
                    page.insert_text(
                        text_pos, 
                        val_str, 
                        fontsize=fontsize, 
                        fontname="helv", 
                        color=(0, 0, 0)
                    )
                    logger.info(f"Populated {placeholder} with '{val_str}' at {text_pos}")
            
            # --- 4. Signature Overlay ---
            if signature_image_bytes:
                logger.info(f"Inserting signature image: {len(signature_image_bytes)} bytes")
                # Using a safe area that avoids the very edges and footer
                SIGNATURE_BOX = fitz.Rect(100, 755, 480, 825)
                page.insert_image(SIGNATURE_BOX, stream=signature_image_bytes)
            else:
                logger.warning("No signature image bytes provided")
            
            # --- 5. Audit Trail ---
            audit_text = (
                f"Digitally signed by: {signer_name} | IP: {ip_address} | "
                f"Date: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | "
                f"Device: {user_agent[:40]}..."
            )
            
            # Absolute bottom
            page.insert_text(
                (86, 835), 
                audit_text,
                fontsize=7,
                color=(0.3, 0.3, 0.3)
            )

            # Return bytes with garbage collection and linear configuration for better web viewing
            return doc.tobytes(garbage=3, deflate=True)
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}", exc_info=True)
            raise
