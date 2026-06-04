# src/web/validators.py
def validate_lead_payload(data):
    """Validates incoming JSON data for creating a lead."""
    if not data:
        return False, "Payload must be valid JSON."
        
    if 'name' not in data or not str(data['name']).strip():
        return False, "Field 'name' is required and cannot be blank."
        
    if 'phone' not in data:
        return False, "Field 'phone' is required."
        
    # Example of advanced business logic validation
    valid_stages = ["New", "Contacted", "Qualified", "Lost", "Won"]
    if 'stage' in data and data['stage'] not in valid_stages:
        return False, f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        
    return True, None

def validate_stage_update(data):
    """Validates incoming JSON data for updating a lead's stage."""
    if not data:
        return False, "Payload must be valid JSON."
        
    if 'stage' not in data:
        return False, "Missing required field: stage"
        
    # Strict validation: Only allow these exact stages
    valid_stages = ["New", "Contacted", "Qualified", "Lost", "Won"]
    if data['stage'] not in valid_stages:
        return False, f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        
    return True, None
