import json
import logging
import uuid
from app.core.logging import (
    StructuredJsonFormatter,
    get_request_id,
    request_id_ctx,
)


def test_response_has_generated_request_id(client):
    """Verify that a request without X-Request-ID receives a generated UUID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    # Ensure it is a valid UUID
    parsed_uuid = uuid.UUID(req_id)
    assert str(parsed_uuid) == req_id


def test_response_preserves_custom_request_id(client):
    """Verify that incoming X-Request-ID header is propagated back to response."""
    custom_id = "custom-client-trace-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_error_response_contains_request_id(client):
    """Verify that 404 or other errors include X-Request-ID in both header and body."""
    custom_id = "err-trace-9999"
    response = client.get("/products/999999", headers={"X-Request-ID": custom_id})
    assert response.status_code == 404
    assert response.headers.get("X-Request-ID") == custom_id
    body = response.json()
    assert body["success"] is False
    assert body["request_id"] == custom_id


def test_structured_json_formatter():
    """Verify that StructuredJsonFormatter outputs valid JSON with request_id and metadata."""
    token = request_id_ctx.set("test-request-id-abc")
    try:
        assert get_request_id() == "test-request-id-abc"
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="User %s performed action",
            args=("alice",),
            exc_info=None,
        )
        record.method = "POST"
        record.path = "/api/v1/test"
        record.status_code = 201

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["request_id"] == "test-request-id-abc"
        assert parsed["message"] == "User alice performed action"
        assert parsed["method"] == "POST"
        assert parsed["path"] == "/api/v1/test"
        assert parsed["status_code"] == 201
        assert "timestamp" in parsed
    finally:
        request_id_ctx.reset(token)
