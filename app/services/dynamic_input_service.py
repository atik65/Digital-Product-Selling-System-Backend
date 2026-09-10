import re
from typing import Dict, Any, List
from app.models.product_input_field import ProductInputField
from app.core.exceptions import ValidationException

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")


class DynamicInputService:
    @staticmethod
    def validate_inputs(
        fields: List[ProductInputField], input_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates client-submitted inputs against configured ProductInputFields.
        Returns sanitized input dictionary or raises ValidationException.
        """
        input_values = input_values or {}
        sanitized: Dict[str, Any] = {}

        for field in fields:
            raw_val = input_values.get(field.name)

            # Check required
            if field.is_required:
                if raw_val is None or (
                    isinstance(raw_val, str) and not raw_val.strip()
                ):
                    raise ValidationException(f"Field '{field.label}' is required")

            if raw_val is not None:
                val_str = str(raw_val).strip()

                # Validate specific types
                if field.type == "email" and val_str:
                    if not EMAIL_REGEX.match(val_str):
                        raise ValidationException(
                            f"Field '{field.label}' must be a valid email address"
                        )

                elif field.type == "number" and val_str:
                    try:
                        float(val_str)
                    except ValueError:
                        raise ValidationException(
                            f"Field '{field.label}' must be a valid numeric value"
                        )

                elif field.type == "url" and val_str:
                    if not URL_REGEX.match(val_str):
                        raise ValidationException(
                            f"Field '{field.label}' must be a valid URL starting with http:// or https://"
                        )

                sanitized[field.name] = val_str

        return sanitized
