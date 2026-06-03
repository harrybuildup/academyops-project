import pytest
from src.models.lead import Lead
from src.models.errors import LeadNotFoundError, DuplicatePhoneError

def test_create_and_get_lead(repo):
    """Verifies that a lead can be created and retrieved accurately."""
    new_lead = Lead(id=None, name="Test User", phone="555-0001", source="Google", stage="New", notes="Test", created_at="", updated_at="")
    repo.add_lead(new_lead)
    
    # Retrieve and verify
    leads = repo.get_all_leads()
    assert len(leads) == 1
    assert leads[0].name == "Test User"
    assert leads[0].phone == "555-0001"

def test_duplicate_phone_handling(repo):
    """Verifies that adding a duplicate phone number raises the correct domain error."""
    lead_one = Lead(id=None, name="User One", phone="555-0002", source="Google", stage="New", notes="", created_at="", updated_at="")
    lead_two = Lead(id=None, name="User Two", phone="555-0002", source="Facebook", stage="New", notes="", created_at="", updated_at="")
    
    repo.add_lead(lead_one)
    
    with pytest.raises(DuplicatePhoneError):
        repo.add_lead(lead_two)

def test_get_lead_not_found(repo):
    """Verifies that querying a non-existent ID raises LeadNotFoundError."""
    with pytest.raises(LeadNotFoundError):
        repo.get_lead_by_id(9999)

def test_update_lead_stage(repo):
    """Verifies that a lead's stage can be updated successfully."""
    lead = Lead(id=None, name="Update User", phone="555-0003", source="Google", stage="New", notes="", created_at="", updated_at="")
    repo.add_lead(lead)
    
    saved_lead = repo.get_all_leads()[0]
    saved_lead.stage = "Contacted"
    repo.update_lead(saved_lead)
    
    updated_lead = repo.get_lead_by_id(saved_lead.id)
    assert updated_lead.stage == "Contacted"

def test_delete_lead(repo):
    """Verifies that a lead can be deleted and raises an error if deleted twice."""
    lead = Lead(id=None, name="Delete User", phone="555-0004", source="Google", stage="New", notes="", created_at="", updated_at="")
    repo.add_lead(lead)
    
    saved_lead = repo.get_all_leads()[0]
    repo.delete_lead(saved_lead.id)
    
    # Verify it is gone
    assert len(repo.get_all_leads()) == 0
    
    # Verify deleting again raises an error
    with pytest.raises(LeadNotFoundError):
        repo.delete_lead(saved_lead.id)