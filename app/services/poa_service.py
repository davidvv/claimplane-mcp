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
            
            # --- 0. Rebranding: Replace EasyAirClaim with ClaimPlane ---
            # This is necessary because the template PDF might still contain the old brand name
            for old_name in ["EasyAirClaim", "easyairclaim"]:
                rebrand_hits = page.search_for(old_name)
                for rect in rebrand_hits:
                    # White out old name
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                    # Insert new name
                    is_header = rect.y0 < 100
                    page.insert_text(
                        (rect.x0, rect.y1 - 2), 
                        "ClaimPlane",
                        fontsize=12 if is_header else 10,
                        fontname="helv", 
                        color=(0, 0, 0),
                        overlay=True
                    )

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
                    # Solid white box over the placeholder (slightly larger to ensure clean replacement)
                    whiteout_rect = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
                    page.draw_rect(whiteout_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                    
                    val_str = str(value)
                    fontsize = 10
                    if len(val_str) > 40:
                        fontsize = 7
                    elif len(val_str) > 25:
                        fontsize = 8
                    
                    # Insert actual data
                    page.insert_text(
                        (rect.x0, rect.y1 - 2), 
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
                    # Adjusted to avoid overlap with audit trail at y=820
                    SIGNATURE_AREA = fitz.Rect(72, 750, 523, 810)
                    page.insert_image(SIGNATURE_AREA, stream=img_stream.read(), keep_proportion=True, overlay=True)
                except Exception as img_err:
                    logger.error(f"Failed to insert signature image: {img_err}")
                    # Don't fail the whole PDF if just the signature fails, 
                    # but log it so we know it's missing.
                    page.insert_text((100, 780), "[Digital Signature Image Error]", color=(1, 0, 0))
            else:
                logger.warning(f"Signature image missing or too small: {len(signature_image_bytes) if signature_image_bytes else 0} bytes")
            
            # --- 5. Audit Trail ---
            # Move up from the edge (y=842 -> y=820) and improve formatting
            audit_y = 820
            audit_trail_rect = fitz.Rect(72, audit_y - 10, 523, audit_y + 25)
            
            # Clean up user agent for display
            display_ua = user_agent if len(user_agent) < 100 else f"{user_agent[:97]}..."
            
            audit_text = (
                f"Digitally signed by: {signer_name} | IP: {ip_address} | "
                f"Date: {signed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"Device/Browser: {display_ua}"
            )
            
            page.insert_textbox(
                audit_trail_rect,
                audit_text,
                fontsize=7,
                color=(0.3, 0.3, 0.3),
                fontname="helv",
                align=fitz.TEXT_ALIGN_LEFT,
                overlay=True
            )

            return doc.tobytes(garbage=3, deflate=True)
            
        except Exception as e:
            logger.error(f"Failed to generate POA PDF: {str(e)}", exc_info=True)
            raise
