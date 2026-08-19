import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_job():
    response = client.post("/jobs", json={
        "design_name": "alu",
        "test_name": "pass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["design_name"] == "alu"
    assert data["test_name"] == "pass"
    assert data["status"] == "QUEUED"

def test_get_job_not_found():
    response = client.get("/jobs/invalid_id")
    assert response.status_code == 404
