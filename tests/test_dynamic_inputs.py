import pytest
from app.models.product_input_field import ProductInputField
from app.services.dynamic_input_service import DynamicInputService
from app.core.exceptions import ValidationException


def test_dynamic_input_validation_success():
    fields = [
        ProductInputField(name="email", label="Account Email", type="email", is_required=True),
        ProductInputField(name="player_id", label="Player ID", type="number", is_required=True),
        ProductInputField(name="profile", label="Profile Name", type="text", is_required=False),
    ]
    inputs = {
        "email": "customer@example.com",
        "player_id": "192837482",
        "profile": "Atik",
    }
    validated = DynamicInputService.validate_inputs(fields, inputs)
    assert validated["email"] == "customer@example.com"
    assert validated["player_id"] == "192837482"
    assert validated["profile"] == "Atik"


def test_dynamic_input_missing_required():
    fields = [
        ProductInputField(name="email", label="Account Email", type="email", is_required=True),
    ]
    inputs = {}
    with pytest.raises(ValidationException) as exc_info:
        DynamicInputService.validate_inputs(fields, inputs)
    assert "required" in str(exc_info.value).lower()


def test_dynamic_input_invalid_email():
    fields = [
        ProductInputField(name="email", label="Account Email", type="email", is_required=True),
    ]
    inputs = {"email": "not-an-email"}
    with pytest.raises(ValidationException) as exc_info:
        DynamicInputService.validate_inputs(fields, inputs)
    assert "valid email" in str(exc_info.value).lower()


def test_dynamic_input_invalid_number():
    fields = [
        ProductInputField(name="player_id", label="Player ID", type="number", is_required=True),
    ]
    inputs = {"player_id": "abc_not_a_number"}
    with pytest.raises(ValidationException) as exc_info:
        DynamicInputService.validate_inputs(fields, inputs)
    assert "numeric" in str(exc_info.value).lower()
