# src/utils/cleansing.py
#
# Phone and source normalisation helpers used by the CSV importer (WP-02).

import re

SOURCE_ALIASES: dict[str, str] = {
    "goog":     "Google",
    "google":   "Google",
    "fb":       "Facebook",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "linked-in":"LinkedIn",
    "website":  "Website",
    "organic":  "Website",
    "referral": "Referral",
}


def normalize_string(value: str) -> str:
    """Strip leading/trailing whitespace."""
    if not value:
        return ""
    return str(value).strip()


def normalize_source(source_raw: str) -> str:
    """Map messy source strings to canonical values. Defaults to 'Website'."""
    cleaned = normalize_string(source_raw).lower()
    return SOURCE_ALIASES.get(cleaned, source_raw.strip() or "Website")


def clean_and_validate_phone(phone_raw: str) -> str:
    """Normalise phone and validate basic plausibility (7-15 digits).

    Returns a normalised digit string (with leading + preserved).
    Raises ValueError for blank or malformed input.
    """
    cleaned = normalize_string(phone_raw)
    if not cleaned:
        raise ValueError("Missing required field: phone number")

    digits_only = re.sub(r"[\s\+\-\(\)]", "", cleaned)

    if not digits_only.isdigit() or not (7 <= len(digits_only) <= 15):
        raise ValueError(f"Malformed phone: '{phone_raw}'")

    return f"+{digits_only}" if cleaned.startswith("+") else digits_only
