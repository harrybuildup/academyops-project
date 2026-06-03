import re

# Canonical mapping directory for source normalization (FR-2)
SOURCE_ALIASES = {
    "goog": "Google",
    "google": "Google",
    "fb": "Facebook",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "linked-in": "LinkedIn",
    "website": "Website",
    "organic": "Website"
}

def normalize_string(value: str) -> str:
    """
    Trims leading/trailing whitespace and standardizes text handling.
    """
    if not value:
        return ""
    return str(value).strip()

def normalize_source(source_raw: str) -> str:
    """
    Maps messy, inconsistent source strings to strict canonical values (FR-2).
    Defaults to 'Website' if an unmapped custom source arrives.
    """
    cleaned = normalize_string(source_raw).lower()
    return SOURCE_ALIASES.get(cleaned, "Website")

def clean_and_validate_phone(phone_raw: str) -> str:
    """
    Normalizes phone formats and enforces basic plausibility rules (FR-3).
    Returns a standardized digit string if valid, or raises ValueError if malformed.
    """
    cleaned = normalize_string(phone_raw)
    if not cleaned:
        raise ValueError("Missing required field: phone number")
        
    # Strip common formatting characters: +, -, (, ), and spaces
    digits_only = re.sub(r"[\s\+\-\(\)]", "", cleaned)
    
    # Plausibility Check: Must be entirely numeric and have a reasonable length (e.g., 7-15 digits)
    if not digits_only.isdigit() or not (7 <= len(digits_only) <= 15):
        raise ValueError(f"Malformed or non-plausible phone format: '{phone_raw}'")
        
    # Return a uniform format (e.g., keeping leading plus if structural, or just normalized digits)
    return f"+{digits_only}" if cleaned.startswith("+") else digits_only