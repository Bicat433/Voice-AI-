"""Shared Pydantic validators."""

import re
from datetime import date

from pydantic import field_validator

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

NAME_PATTERN = re.compile(r"^[A-Za-z\-']{1,50}$")
ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")
ALPHANUMERIC_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


def normalize_phone(value: str) -> str:
    """Strip non-digits and validate US 10-digit phone number."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone number must be a valid US 10-digit number")
    return digits


def validate_name(value: str, field_label: str = "Name") -> str:
    if not NAME_PATTERN.match(value):
        raise ValueError(
            f"{field_label} must be 1-50 characters and contain only letters, hyphens, or apostrophes"
        )
    return value


def validate_state(value: str) -> str:
    upper = value.upper()
    if upper not in US_STATES:
        raise ValueError("State must be a valid 2-letter US abbreviation")
    return upper


def validate_zip_code(value: str) -> str:
    if not ZIP_PATTERN.match(value):
        raise ValueError("Zip code must be 5 digits or ZIP+4 format (12345 or 12345-6789)")
    return value


def validate_dob(value: date) -> date:
    if value > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return value


def validate_alphanumeric(value: str) -> str:
    if not ALPHANUMERIC_PATTERN.match(value):
        raise ValueError("Insurance member ID must be alphanumeric")
    return value
