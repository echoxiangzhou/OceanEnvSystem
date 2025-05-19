import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_thermocline():
    data = {
        "depth": [0, 10, 20, 30, 40, 50],
        "profile": [25, 24, 20, 15, 12, 10],
        "cline_type": "temperature",
        "window_size": 5
    }
    resp = client.post("/api/v1/diagnostics/cline/detect", json=data)
    assert resp.status_code == 200
    assert "cline_depth" in resp.json()
