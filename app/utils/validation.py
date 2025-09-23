"""Validation utilities for the Flight Compensation Claim API."""

import re
from datetime import datetime, date
from typing import Optional

from pydantic import EmailStr


def validate_flight_number(flight_number: str) -> bool:
    """Validate flight number format.
    
    Flight number should be in format: XX1234 or XX123
    where XX are 2 uppercase letters and 1234 are 3-4 digits.
    
    Args:
        flight_number: Flight number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not flight_number:
        return False
    
    # Pattern: 2 uppercase letters followed by 3-4 digits
    pattern = r"^[A-Z]{2}\d{3,4}$"
    return bool(re.match(pattern, flight_number))


def validate_iata_code(code: str) -> bool:
    """Validate IATA airport code.
    
    IATA codes are 3 uppercase letters.
    
    Args:
        code: Airport code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not code:
        return False
    
    # Pattern: exactly 3 uppercase letters
    pattern = r"^[A-Z]{3}$"
    return bool(re.match(pattern, code))


def validate_booking_reference(reference: str) -> bool:
    """Validate booking reference format.
    
    Booking references should be at least 6 characters long
    and typically contain alphanumeric characters.
    
    Args:
        reference: Booking reference to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not reference:
        return False
    
    # Minimum 6 characters
    if len(reference) < 6:
        return False
    
    # Should contain alphanumeric characters
    if not re.match(r"^[A-Za-z0-9]+$", reference):
        return False
    
    return True


def validate_email_domain(email: EmailStr, allowed_domains: Optional[list] = None) -> bool:
    """Validate email domain.
    
    Args:
        email: Email address to validate
        allowed_domains: List of allowed domains (optional)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    domain = email.split('@')[1].lower()
    
    if allowed_domains:
        return domain in [d.lower() for d in allowed_domains]
    
    # Basic validation - reject obvious fake domains
    fake_domains = ['example.com', 'test.com', 'fake.com', 'tempmail.com']
    return domain not in fake_domains


def validate_flight_date(flight_date: date) -> bool:
    """Validate flight date.
    
    Flight date should be in the past (for claims) and not too old.
    
    Args:
        flight_date: Flight date to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not flight_date:
        return False
    
    today = date.today()
    
    # Flight date should not be in the future
    if flight_date > today:
        return False
    
    # Flight date should not be more than 3 years old (EU regulation limit)
    three_years_ago = date(today.year - 3, today.month, today.day)
    if flight_date < three_years_ago:
        return False
    
    return True


def validate_disruption_type(disruption_type: str) -> bool:
    """Validate disruption type.
    
    Args:
        disruption_type: Type of disruption
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_types = {
        "delay", "cancellation", "denied boarding", "downgrade",
        "flight delay", "flight cancellation", "overbooking"
    }
    
    return disruption_type.lower() in valid_types


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format.
    
    Basic international phone number validation.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return True  # Phone is optional
    
    # Remove common separators
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Should contain only digits
    if not re.match(r'^\d+$', cleaned_phone):
        return False
    
    # Should be between 7 and 15 digits
    if len(cleaned_phone) < 7 or len(cleaned_phone) > 15:
        return False
    
    return True


def validate_file_size(file_size_bytes: int, max_size_mb: int = 5) -> bool:
    """Validate file size.
    
    Args:
        file_size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not file_size_bytes or file_size_bytes <= 0:
        return False
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_size_bytes


def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """Validate file type by extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: Set of allowed file extensions
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not filename:
        return False
    
    file_extension = filename.lower().split('.')[-1]
    return f".{file_extension}" in allowed_extensions


def validate_claim_status(status: str) -> bool:
    """Validate claim status.
    
    Args:
        status: Claim status to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_statuses = {
        "submitted", "under_review", "approved", "rejected", 
        "resolved", "in_process", "pending"
    }
    
    return status.lower() in valid_statuses


def validate_declaration_accepted(accepted: bool) -> bool:
    """Validate that declaration has been accepted.
    
    Args:
        accepted: Declaration acceptance status
        
    Returns:
        bool: True if accepted, False otherwise
    """
    return accepted is True


def validate_consent_accepted(accepted: bool) -> bool:
    """Validate that consent has been accepted.
    
    Args:
        accepted: Consent acceptance status
        
    Returns:
        bool: True if accepted, False otherwise
    """
    return accepted is True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and special characters
    sanitized = re.sub(r'[<>:\"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250] + ext
    
    return sanitized


def validate_flight_distance(distance_km: int) -> str:
    """Validate flight distance and return compensation category.
    
    Args:
        distance_km: Flight distance in kilometers
        
    Returns:
        str: Compensation category (short, medium, long)
    """
    if distance_km < 1500:
        return "short"
    elif distance_km < 3500:
        return "medium"
    else:
        return "long"


def calculate_compensation_amount(distance_km: int, delay_hours: int) -> int:
    """Calculate compensation amount based on distance and delay.
    
    Args:
        distance_km: Flight distance in kilometers
        delay_hours: Delay duration in hours
        
    Returns:
        int: Compensation amount in EUR
    """
    if delay_hours < 3:
        return 0
    
    category = validate_flight_distance(distance_km)
    
    if category == "short":
        return 250
    elif category == "medium":
        return 400
    else:  # long
        return 600


def validate_timeline_event(event: str) -> bool:
    """Validate timeline event description.
    
    Args:
        event: Event description
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not event or len(event.strip()) < 5:
        return False
    
    if len(event) > 500:
        return False
    
    return True


def validate_session_id(session_id: str) -> bool:
    """Validate chat session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not session_id:
        return False
    
    # Should start with 'sess_' followed by alphanumeric characters
    pattern = r"^sess_[a-zA-Z0-9]+$"
    return bool(re.match(pattern, session_id))


# Import os for sanitize_filename function
import os