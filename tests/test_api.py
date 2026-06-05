"""tests/test_api.py — HTTP-level tests for the FastAPI application."""

BASE = "/api/v1/leads"


def _create(client, **overrides):
    payload = {"name": "Test User", "phone": "5550001", "source": "Google", "notes": "", **overrides}
    return client.post(BASE, json=payload)


# --- Health ---

def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


# --- Create ---

def test_create_lead_success(client):
    res = _create(client)
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Test User"
    assert body["stage"] == "New"
    assert body["id"] is not None


def test_create_lead_missing_name(client):
    assert client.post(BASE, json={"phone": "5550002"}).status_code == 422


def test_create_lead_missing_phone(client):
    assert client.post(BASE, json={"name": "No Phone"}).status_code == 422


def test_create_lead_duplicate_phone(client):
    _create(client, phone="5550003")
    res = _create(client, name="Other", phone="5550003")
    assert res.status_code == 400
    assert "already exists" in res.json()["error"].lower()


# --- List ---

def test_list_leads_empty(client):
    res = client.get(BASE)
    assert res.status_code == 200
    assert res.json()["meta"]["total_count"] == 0
    assert res.json()["data"] == []


def test_list_leads_returns_created(client):
    _create(client, phone="5550010")
    _create(client, name="Second", phone="5550011")
    body = client.get(BASE).json()
    assert body["meta"]["total_count"] == 2
    assert len(body["data"]) == 2


def test_list_leads_filter_by_stage(client):
    _create(client, phone="5550020")
    res2 = _create(client, name="B", phone="5550021")
    lead_id = res2.json()["id"]
    client.patch(f"{BASE}/{lead_id}/stage", json={"stage": "Contacted"})

    body = client.get(BASE, params={"stage": "Contacted"}).json()
    assert body["meta"]["total_count"] == 1
    assert body["data"][0]["stage"] == "Contacted"


def test_list_leads_filter_by_source(client):
    _create(client, phone="5550030", source="Google")
    _create(client, name="B", phone="5550031", source="Facebook")
    body = client.get(BASE, params={"source": "Facebook"}).json()
    assert body["meta"]["total_count"] == 1


def test_list_leads_pagination(client):
    for i in range(5):
        _create(client, name=f"Lead {i}", phone=f"555004{i}")
    body = client.get(BASE, params={"page": 1, "limit": 2}).json()
    assert body["meta"]["total_count"] == 5
    assert body["meta"]["total_pages"] == 3
    assert len(body["data"]) == 2


# --- Get single ---

def test_get_lead_success(client):
    created = _create(client, phone="5550050").json()
    res = client.get(f"{BASE}/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_lead_not_found(client):
    res = client.get(f"{BASE}/9999")
    assert res.status_code == 404
    assert "error" in res.json()


# --- Update stage ---

def test_update_stage_success(client):
    created = _create(client, phone="5550060").json()
    res = client.patch(f"{BASE}/{created['id']}/stage", json={"stage": "Qualified"})
    assert res.status_code == 200
    assert res.json()["stage"] == "Qualified"


def test_update_stage_invalid_value(client):
    created = _create(client, phone="5550061").json()
    res = client.patch(f"{BASE}/{created['id']}/stage", json={"stage": "Purchased"})
    assert res.status_code == 422


def test_update_stage_not_found(client):
    res = client.patch(f"{BASE}/9999/stage", json={"stage": "Enrolled"})
    assert res.status_code == 404


# --- Delete ---

def test_delete_lead_success(client):
    created = _create(client, phone="5550070").json()
    assert client.delete(f"{BASE}/{created['id']}").status_code == 204


def test_delete_lead_not_found(client):
    assert client.delete(f"{BASE}/9999").status_code == 404


def test_delete_then_get_returns_404(client):
    created = _create(client, phone="5550071").json()
    client.delete(f"{BASE}/{created['id']}")
    assert client.get(f"{BASE}/{created['id']}").status_code == 404
