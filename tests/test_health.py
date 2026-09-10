def test_health_check(client):
    """Test the /health endpoint returns 200 OK and connected database status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["status_code"] == 200
    assert data["message"] == "Service is healthy"
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database"] == "connected"
    assert "version" in data["data"]
    assert "timestamp" in data["data"]
