import pytest

# Define the base route once. Change this one line to upgrade the API version later.
BASE_URL = "/api/v1/leads"

def test_create_lead_success(client):
    """Verifies that a valid POST request creates a lead and returns a 201 status."""
    payload = {
        "name": "API User",
        "phone": "555-9001",
        "source": "Website",
        "stage": "New",
        "notes": "Testing API creation"
    }
    
    response = client.post(BASE_URL, json=payload)
    
    assert response.status_code == 201
    assert "Lead created successfully" in response.get_json()["message"]

def test_create_lead_validation_error(client):
    """Verifies that missing required fields result in a 400 Bad Request."""
    payload = {"name": "Incomplete User"}
    
    response = client.post(BASE_URL, json=payload)
    assert response.status_code == 400

def test_get_all_leads(client):
    """Verifies that a GET request returns a list of leads inside the data wrapper."""
    client.post(BASE_URL, json={
        "name": "List User", "phone": "555-9002", "source": "Referral", "stage": "New", "notes": ""
    })
    
    response = client.get(BASE_URL)
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert "meta" in data
    assert "data" in data
    assert len(data["data"]) >= 1

def test_get_lead_not_found(client):
    """Verifies that requesting a non-existent lead ID returns a 404 Not Found."""
    response = client.get(f"{BASE_URL}/9999")
    assert response.status_code == 404

def test_update_lead_success(client):
    """Verifies that a PATCH request successfully updates an existing lead's stage."""
    client.post(BASE_URL, json={
        "name": "Update Target", "phone": "555-9003", "source": "Ads", "stage": "New", "notes": ""
    })
    
    leads = client.get(BASE_URL).get_json()["data"]
    lead_id = leads[-1]["id"]
    
    # Dynamically inject the ID and the endpoint route
    update_res = client.patch(f"{BASE_URL}/{lead_id}/stage", json={"stage": "Contacted"})
    assert update_res.status_code == 200
    
    verify_res = client.get(f"{BASE_URL}/{lead_id}").get_json()
    assert verify_res["stage"] == "Contacted"

def test_delete_lead_success(client):
    """Verifies that a DELETE request removes the lead successfully."""
    client.post(BASE_URL, json={
        "name": "Delete Target", "phone": "555-9004", "source": "Organic", "stage": "New", "notes": ""
    })
    
    leads = client.get(BASE_URL).get_json()["data"]
    lead_id = leads[-1]["id"]
    
    delete_res = client.delete(f"{BASE_URL}/{lead_id}")
    assert delete_res.status_code == 204
    
    verify_res = client.get(f"{BASE_URL}/{lead_id}")
    assert verify_res.status_code == 404