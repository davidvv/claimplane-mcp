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
            page = doc[0]
            
            # --- 1. Aggressive Redaction of Template Artifacts ---
            
            # Redact the large signature box area
            # SIGNATURE header y ~ 728. Audit trail footer y ~ 841.
            sig_box_rect = fitz.Rect(50, 745, 545, 840)
            page.add_redact_annot(sig_box_rect, fill=(1, 1, 1))
            
            # Redact specific UI text placeholders
            ui_placeholders = ["[Electronic Signature Will Be Placed Here]", "{{audit_trail_id}}"]
            for ui_p in ui_placeholders:
                hits = page.search_for(ui_p)
                for rect in hits:
                    page.add_redact_annot(rect, fill=(1, 1, 1))

            # Apply these redactions before adding new content
            page.apply_redactions()

            # --- 2. Data Preparation ---
            if additional_passengers:
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

            # --- 3. Content Insertion (Overlay) ---
            
            # We don't redact data placeholders anymore as it was too aggressive
            # Instead, we just draw white boxes over them right before inserting text
            for placeholder, value in replacements.items():
                hits = page.search_for(placeholder)
                for rect in hits:
                    # Solid white box over the placeholder
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                    
                    val_str = str(value)
                    fontsize = 10
                    if len(val_str) > 40:
                        fontsize = 7
                    elif len(val_str) > 25:
                        fontsize = 8
                    
                    # Insert actual data
                    page.insert_text(
                        (rect.x0, rect.y1 - 1), 
                        val_str, 
                        fontsize=fontsize, 
                        fontname="helv", 
                        color=(0, 0, 0),
                        overlay=True
                    )
            
            # --- 4. Signature Image ---
            if signature_image_bytes and len(signature_image_bytes) > 50:
                try:
                    logger.info(f"Inserting signature image: {len(signature_image_bytes)} bytes")
                    # Using Pixmap to validate image data before insertion
                    img_stream = io.BytesIO(signature_image_bytes)
                    # Position it within the large cleared signature area
                    SIGNATURE_AREA = fitz.Rect(72, 750, 523, 830)
                    page.insert_image(SIGNATURE_AREA, stream=img_stream.read(), keep_proportion=True, overlay=True)
                except Exception as img_err:
                    logger.error(f"Failed to insert signature image: {img_err}")
                    # Don't fail the whole PDF if just the signature fails, 
                    # but log it so we know it's missing.
                    page.insert_text((100, 780), "[Digital Signature Image Error]", color=(1, 0, 0))
            else:
                logger.warning(f"Signature image missing or too small: {len(signature_image_bytes) if signature_image_bytes else 0} bytes")
            
            # --- 5. Audit Trail ---
            audit_text = (
                f"Digitally signed by: {signer_name} | IP: {ip_address} | "
                f"Date: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | "
                f"Device: {user_agent[:40]}..."
            )
            
            page.insert_text(
                (86, 842), 
                audit_text,
                fontsize=7,
                color=(0.2, 0.2, 0.2),
                fontname="helv",
                overlay=True
            )

            return doc.tobytes(garbage=3, deflate=True)
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}", exc_info=True)
            raise
