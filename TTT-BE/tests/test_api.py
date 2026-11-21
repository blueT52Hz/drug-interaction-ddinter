from dataclasses import replace

from app.core import security


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["stats"]["drugs"] == 6


def test_check_interactions(client):
    response = client.post("/interactions/check", json={"registrationNumbers": ["REG-WARFARIN", "REG-ASPIRIN"]})

    assert response.status_code == 200
    body = response.json()
    assert body["hasMajor"] is True
    assert body["interactions"][0]["severity"] == "major"


def test_check_rejects_empty_list(client):
    response = client.post("/interactions/check", json={"registrationNumbers": []})

    assert response.status_code == 422


def test_drug_warnings(client):
    response = client.post("/drug-warnings", json={"registrationNumbers": ["REG-WARFARIN", "NOPE"]})

    assert response.status_code == 200
    body = response.json()
    assert body["notFound"] == ["NOPE"]
    assert body["drugs"][0]["foods"][0]["foodName"] == "spinach"
    assert body["drugs"][0]["diseases"] == []


def test_internal_key_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(security, "settings", replace(security.settings, internal_key="secret"))

    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"X-Internal-Key": "wrong"}).status_code == 401
    assert client.get("/health", headers={"X-Internal-Key": "secret"}).status_code == 200
