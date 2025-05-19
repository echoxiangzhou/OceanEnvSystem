import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_oi_fusion():
    data = {
        "obs_coords": [[0,0],[1,0],[0,1]],
        "obs_values": [1.0, 2.0, 1.5],
        "interp_coords": [[0.5,0.5],[1,1]],
        "sigma2": 1.0,
        "L": 1.0,
        "noise": 1e-6
    }
    resp = client.post("/api/v1/fusion/oi/run", json=data)
    assert resp.status_code == 200
    assert "interp_values" in resp.json()
