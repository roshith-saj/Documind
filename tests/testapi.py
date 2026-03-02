import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "DocuMind" in r.json()["message"]


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "services" in data


def test_list_documents_empty():
    r = client.get("/api/v1/documents/")
    assert r.status_code == 200
    assert r.json() == []


def test_query_stub():
    r = client.post("/api/v1/query/", json={"question": "What is this document about?"})
    assert r.status_code == 200
    data = r.json()
    assert data["question"] == "What is this document about?"
    assert "answer" in data
    assert "latency_ms" in data


def test_upload_unsupported_type():
    r = client.post(
        "/api/v1/documents/",
        files={"file": ("test.xyz", b"content", "application/octet-stream")},
    )
    assert r.status_code == 415