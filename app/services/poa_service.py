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
    # These are approximate based on the generation script
    # x0, y0, x1, y1 (PyMuPDF uses top-left as 0,0 usually? No, PDF is bottom-left 0,0 standard, 
    # but PyMuPDF rects are usually (x0, y0, x1, y1) where y increases downwards in some contexts, 
    # but for PDF page.insert_image, it uses PDF coordinates where (0,0) is usually bottom-left.
    # Wait, PyMuPDF documentation says: Point(0, 0) is top-left corner of the page.
    SIGNATURE_RECT = fitz.Rect(72, 600, 523, 680) 
    
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
            # We'll use page.search_for() to find placeholders and overlay text
            # Or we can just draw text over the white space if we know coordinates
            # But search_for is more robust if we used exact placeholders in the template
            
            replacements = {
                "{{flight_number}}": flight_number,
                "{{flight_date}}": flight_date,
                "{{departure_airport}}": departure_airport,
                "{{arrival_airport}}": arrival_airport,
                "{{booking_reference}}": booking_reference,
                "{{primary_passenger_name}}": primary_passenger_name,
                "{{additional_passengers}}": additional_passengers or "None",
                "{{address}}": address,
                "{{signer_name}}": signer_name,
                "{{signed_date}}": signed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
            # Simple text overlay strategy:
            # 1. Find the placeholder text
            # 2. Draw a white rectangle over it to "erase" it (optional, if placeholder is visible)
            # 3. Insert the new text
            
            for placeholder, value in replacements.items():
                hits = page.search_for(placeholder)
                for rect in hits:
                    # Draw white box to cover placeholder
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    # Insert new text (fontsize 10 to match template)
                    page.insert_text((rect.x0, rect.y1 - 2), str(value), fontsize=10, fontname="Helvetica")

            # --- Signature Overlay ---
            # Insert the signature image
            # We use the defined constant rect
            page.insert_image(POAService.SIGNATURE_RECT, stream=signature_image_bytes)
            
            # --- Audit Trail ---
            audit_text = (
                f"Signed by: {signer_name} | IP: {ip_address} | "
                f"Time: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | "
                f"UA: {user_agent[:50]}..."
            )
            
            # Find the footer placeholder or just write at bottom
            footer_hits = page.search_for("{{audit_trail_id}}")
            if footer_hits:
                rect = footer_hits[0]
                # Cover the whole footer line ideally, or just the ID part
                # Let's just write the full audit trail at the bottom center
                page.insert_text(
                    (72, 800), # Near bottom
                    audit_text,
                    fontsize=6,
                    color=(0.5, 0.5, 0.5)
                )
            
            # Return bytes
            return doc.tobytes()
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}")
            raise

