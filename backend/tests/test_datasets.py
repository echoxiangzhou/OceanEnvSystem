import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_get_dataset():
    data = {
        "name": "Test Dataset",
        "description": "For testing",
        "source_type": "BUOY",
        "data_type": "OBSERVATIONS",
        "spatial_coverage": {"type": "Point", "coordinates": [120, 30]},
        "temporal_coverage": {"start": "2023-01-01T00:00:00Z", "end": "2023-01-02T00:00:00Z"},
        "variables": [{"name": "temperature", "unit": "degC"}],
        "file_format": "nc",
        "file_location": "test.nc"
    }
    resp = client.post("/api/v1/datasets", json=data)
    assert resp.status_code == 200
    dataset = resp.json()
    assert dataset["name"] == "Test Dataset"

    # 查询
    resp2 = client.get(f"/api/v1/datasets/{dataset['id']}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == dataset["id"]
