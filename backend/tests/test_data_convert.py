import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

def test_csv_to_netcdf():
    csv_content = "a,b\n1,2\n3,4\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    data = {"file_type": "csv"}
    resp = client.post("/api/v1/data/convert", files=files, data=data)
    assert resp.status_code == 200
    assert "netcdf_path" in resp.json()
