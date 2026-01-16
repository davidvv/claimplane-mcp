"""
Email Parsing Service for extracting content from .eml files.
"""
import email
import re
from email.message import Message
from typing import Dict, Any, Optional

class EmailParserService:
    """Service to parse raw email files and extract relevant content."""

    @staticmethod
    def parse_eml(file_content: bytes) -> Dict[str, Any]:
        """
        Parse .eml content bytes and extract subject, date, sender, and body.

        Args:
            file_content: Raw bytes of the .eml file

        Returns:
            Dictionary containing email metadata and body
        """
        try:
            msg = email.message_from_bytes(file_content)
            
            # Extract metadata
            subject = msg.get("Subject", "")
            from_addr = msg.get("From", "")
            date = msg.get("Date", "")
            
            # Extract body
            body = EmailParserService._extract_body(msg)
            
            return {
                "subject": subject,
                "from": from_addr,
                "date": date,
                "body": body
            }
        except Exception as e:
            raise ValueError(f"Failed to parse email content: {str(e)}")

    @staticmethod
    def _extract_body(msg: Message) -> str:
        """Extract the plain text body from the email message."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    try:
                        part_body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                        return EmailParserService._clean_text(part_body)
                    except Exception:
                        continue
                elif content_type == "text/html" and not body:
                    # Fallback to HTML if no plain text found yet
                    try:
                        part_body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                        # Simple tag stripping
                        body = EmailParserService._strip_html(part_body)
                    except Exception:
                        continue
        else:
            # Not multipart
            try:
                content = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
                if msg.get_content_type() == "text/html":
                    body = EmailParserService._strip_html(content)
                else:
                    body = EmailParserService._clean_text(content)
            except Exception:
                pass

        return body

    @staticmethod
    def _strip_html(html_content: str) -> str:
        """Remove HTML tags using regex (simple fallback since BeautifulSoup not available)."""
        # Remove script and style elements
        clean = re.sub(r'<(script|style).*?</\1>(?s)', '', html_content)
        # Remove tags
        clean = re.sub(r'<[^>]+>', ' ', clean)
        # Fix spacing
        return EmailParserService._clean_text(clean)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize whitespace and clean text."""
        # Replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
