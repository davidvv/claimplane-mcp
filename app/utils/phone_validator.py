"""Phone number validation and normalization utilities."""
import re
from typing import Optional


def normalize_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Normalize a phone number by removing all spaces and whitespace.

    Args:
        phone: Phone number string (may contain spaces)

    Returns:
        Normalized phone number without spaces, or None if input is None/empty

    Examples:
        "+34 612 345 678" -> "+34612345678"
        "+1 (555) 123 4567 " -> "+1(555)1234567"
        "  +44 20 7946 0958  " -> "+442079460958"
    """
    if not phone:
        return None

    # Remove all whitespace characters (spaces, tabs, newlines)
    normalized = re.sub(r'\s+', '', phone)

    # Return None if the result is empty after normalization
    if not normalized:
        return None

    return normalized


def validate_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Validate and normalize a phone number.

    Rules:
    - Must start with + followed by country code
    - Can contain digits, parentheses, and hyphens
    - After normalization (removing spaces), must have 8-15 digits
    - No spaces allowed in final normalized form

    Args:
        phone: Phone number string to validate

    Returns:
        Normalized phone number if valid, or None if input is None

    Raises:
        ValueError: If phone number format is invalid

    Examples:
        Valid:
            "+34 612 345 678" -> "+34612345678"
            "+1-555-123-4567" -> "+1-555-123-4567"
            "+44 (20) 7946 0958" -> "+44(20)79460958"
        Invalid:
            "612345678" (missing country code)
            "+34 abc" (contains letters)
            "+1 23" (too short)
    """
    if phone is None or phone == "":
        return None

    # Normalize: remove all spaces
    normalized = normalize_phone_number(phone)

    if not normalized:
        raise ValueError("Phone number cannot be empty or only whitespace")

    # Check if it starts with +
    if not normalized.startswith('+'):
        raise ValueError("Phone number must start with + followed by country code (e.g., +34, +1, +44)")

    # Check for invalid characters (allow only digits, +, -, (, ))
    if not re.match(r'^\+[\d\-()]+$', normalized):
        raise ValueError("Phone number can only contain digits, +, -, ( and ) characters")

    # Extract only digits (excluding the leading +)
    digits_only = re.sub(r'[^\d]', '', normalized)

    # Validate length (typical range: 8-15 digits for international numbers)
    # Country code (1-3 digits) + subscriber number (7-12 digits)
    if len(digits_only) < 8:
        raise ValueError(f"Phone number too short. Must have at least 8 digits (found {len(digits_only)})")

    if len(digits_only) > 15:
        raise ValueError(f"Phone number too long. Must have at most 15 digits (found {len(digits_only)})")

    return normalized
