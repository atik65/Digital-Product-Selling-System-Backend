"""
Script to generate a comprehensive, production-ready Postman Collection v2.1.0 JSON file
for the Digital Product Selling System API directly from the FastAPI application and OpenAPI schema.
"""

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app


def resolve_schema(
    schema: Dict[str, Any], components: Dict[str, Any]
) -> Dict[str, Any]:
    """Recursively resolve $ref pointers in OpenAPI schemas."""
    if "$ref" in schema:
        ref_path = schema["$ref"].replace("#/components/schemas/", "")
        if ref_path in components:
            return resolve_schema(components[ref_path], components)
    if "allOf" in schema:
        merged: Dict[str, Any] = {}
        for sub in schema["allOf"]:
            res = resolve_schema(sub, components)
            merged.update(res)
            if "properties" in res:
                merged.setdefault("properties", {}).update(res["properties"])
        return merged
    if "anyOf" in schema:
        for sub in schema["anyOf"]:
            if sub.get("type") != "null":
                return resolve_schema(sub, components)
    return schema


def generate_sample_from_schema(
    schema: Dict[str, Any], components: Dict[str, Any], field_name: str = ""
) -> Any:
    """Generate realistic sample values based on schema types, format, and field names."""
    schema = resolve_schema(schema, components)
    schema_type = schema.get("type")

    # Handle enums
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    # Handle default or example
    if "example" in schema:
        return schema["example"]
    if "default" in schema and schema["default"] is not None:
        return schema["default"]

    # Handle objects
    if schema_type == "object" or "properties" in schema:
        props = schema.get("properties", {})
        obj: Dict[str, Any] = {}
        for p_name, p_schema in props.items():
            obj[p_name] = generate_sample_from_schema(p_schema, components, p_name)
        return obj

    # Handle arrays
    if schema_type == "array":
        items_schema = schema.get("items", {})
        return [generate_sample_from_schema(items_schema, components, field_name)]

    # Handle strings
    if schema_type == "string":
        fmt = schema.get("format", "")
        if fmt == "date-time":
            return "2026-10-01T12:00:00Z"
        if fmt == "email" or "email" in field_name.lower():
            return "customer@example.com"
        if fmt == "password" or "password" in field_name.lower():
            return "Secret123!"
        if "phone" in field_name.lower():
            return "+8801700000000"
        if "slug" in field_name.lower():
            return "sample-item-slug"
        if "url" in field_name.lower() or "image" in field_name.lower():
            return "https://example.com/media/sample.png"
        if "code" in field_name.lower() and "coupon" in field_name.lower():
            return "DISCOUNT20"
        if "trx" in field_name.lower():
            return "TRX99887766"
        if "token" in field_name.lower():
            return "sample_oauth_or_jwt_token_string"
        if "status" in field_name.lower():
            return "PENDING"
        if "type" in field_name.lower():
            return "PERCENTAGE"
        if "role" in field_name.lower():
            return "customer"
        return f"sample_{field_name}" if field_name else "sample text"

    # Handle numbers/integers
    if schema_type in ("integer", "number"):
        if (
            "price" in field_name.lower()
            or "amount" in field_name.lower()
            or "balance" in field_name.lower()
        ):
            return 250.0 if schema_type == "number" else 250
        if "quantity" in field_name.lower() or "limit" in field_name.lower():
            return 1
        if "id" in field_name.lower():
            return 1
        if "order" in field_name.lower():
            return 0
        return 100 if schema_type == "integer" else 99.99

    # Handle booleans
    if schema_type == "boolean":
        return True

    return None


CUSTOM_EXAMPLES = {
    "/api/v1/auth/admin/login": {
        "email": "admin@boostghor.com",
        "password": "adminpassword123",
    },
    "/api/v1/auth/google": {
        "id_token": "google_oauth2_id_token_from_client",
        "phone": "+8801712345678",
    },
    "/api/v1/auth/refresh": {"refresh_token": "{{refresh_token}}"},
    "/api/v1/auth/me": {"username": "customer_updated", "phone": "+8801799887766"},
    "/api/v1/admin/categories": {
        "name": "Game Credits & Top-Up",
        "slug": "game-credits",
        "icon": "https://example.com/icons/game.png",
        "sort_order": 1,
        "is_active": True,
    },
    "/api/v1/admin/products": {
        "category_id": 1,
        "name": "Free Fire Diamond",
        "slug": "free-fire-diamond",
        "description": "Instant in-game Free Fire Diamond top-up via Player ID.",
        "image": "https://example.com/images/freefire.png",
        "is_active": True,
    },
    "/api/v1/admin/products/{product_id}/inputs": {
        "name": "player_id",
        "label": "Player ID (UID)",
        "type": "text",
        "placeholder": "Enter your 9-10 digit Player ID",
        "is_required": True,
        "sort_order": 1,
    },
    "/api/v1/admin/products/{product_id}/packages": {
        "name": "115 Diamonds",
        "price": 85.0,
        "original_price": 95.0,
        "in_stock": True,
        "is_active": True,
        "sort_order": 1,
    },
    "/api/v1/coupons/validate": {"code": "SUMMER20", "package_id": 1, "quantity": 1},
    "/api/v1/admin/coupons": {
        "code": "SUMMER20",
        "type": "PERCENTAGE",
        "value": 20.0,
        "max_discount": 50.0,
        "minimum_order_amount": 200.0,
        "usage_limit": 100,
        "per_user_limit": 1,
        "is_active": True,
        "expires_at": "2026-12-31T23:59:59Z",
    },
    "/api/v1/orders/checkout": {
        "package_id": 1,
        "quantity": 1,
        "customer_inputs": {"player_id": "1829384920"},
        "coupon_code": "SUMMER20",
        "use_wallet": False,
    },
    "/api/v1/admin/orders/{order_id}/status": {
        "status": "COMPLETED",
        "admin_notes": "Diamonds transferred successfully to UID 1829384920.",
    },
    "/api/v1/admin/payment-methods": {
        "name": "bKash Personal",
        "code": "BKASH_MANUAL",
        "type": "MANUAL",
        "account_number": "01700112233",
        "instructions": "Send Money to this personal bKash number and enter TrxID below.",
        "qr_code_image": "https://example.com/qr/bkash.png",
        "is_active": True,
    },
    "/api/v1/payments/initiate": {"order_id": 1, "payment_method_id": 1},
    "/api/v1/payments/verify-manual": {
        "payment_id": 1,
        "transaction_id": "TRX987654321",
        "sender_phone": "+8801700112233",
    },
    "/api/v1/payments/webhook/sms": {
        "sender": "bKash",
        "message": "You have received Tk 500.00 from 01711223344. Fee Tk 0.00. Balance Tk 5,234.00. TrxID 9K48X78L9 at 11/09/2026 02:20",
        "sim_slot": 1,
        "device_id": "phone-galaxy-a12",
        "timestamp": 1726000000,
    },
    "/api/v1/admin/payments/{payment_id}/verify": {
        "status": "COMPLETED",
        "admin_notes": "Verified bKash statement.",
    },
    "/api/v1/wallet/topup": {
        "amount": 500.0,
        "payment_method_id": 1,
        "transaction_id": "TRX_TOPUP_8899",
        "sender_phone": "+8801700112233",
    },
    "/api/v1/admin/wallet/topups/{topup_id}/approve": {
        "admin_notes": "Received 500 BDT via bKash."
    },
    "/api/v1/admin/wallet/topups/{topup_id}/reject": {
        "admin_notes": "Invalid transaction ID. Money not received."
    },
    "/api/v1/admin/lotteries": {
        "title": "Mega Weekly Lucky Spin",
        "description": "Buy a ticket for 50 BDT and win up to 5,000 Diamonds!",
        "ticket_price": 50.0,
        "total_tickets": 100,
        "start_date": "2026-10-01T00:00:00Z",
        "end_date": "2026-10-07T23:59:59Z",
        "is_active": True,
    },
    "/api/v1/admin/lotteries/{lottery_id}/prizes": {
        "rank": 1,
        "prize_title": "Grand Prize: 5,000 Diamonds",
        "prize_type": "diamonds",
        "prize_value": "5000",
    },
    "/api/v1/admin/banners": {
        "image": "https://example.com/banners/summer_sale.png",
        "title": "Summer Super Sale",
        "description": "50% off on premium passes and streaming accounts!",
        "button_text": "Shop Now",
        "button_url": "/category/game-credits",
        "is_active": True,
        "sort_order": 1,
    },
    "/api/v1/admin/popups": {
        "title": "Special Flash Promo!",
        "content": "Use coupon FLASH15 for instant 15% discount on all game credits today!",
        "is_active": True,
    },
    "/api/v1/admin/settings": {
        "site_name": "Digital Product Selling System",
        "support_phone": "+8801999888777",
        "support_email": "support@boostghor.com",
        "telegram_url": "https://t.me/boostghorsupport",
        "whatsapp_url": "https://wa.me/8801999888777",
        "notice_text": "Notice: bKash payment gateway maintenance on Sunday 2 AM - 4 AM.",
    },
    "/api/v1/admin/users/{user_id}/role": {"role": "admin"},
}


def determine_role(path: str, summary: str, description: str) -> str:
    """Determine the access level for an endpoint."""
    if "/auth/admin/login" in path:
        return "Public (Admin Login)"
    if "/auth/google" in path or "/auth/refresh" in path:
        return "Public"
    if "/admin" in path:
        return "Admin"
    if any(
        k in path
        for k in (
            "/auth/me",
            "/orders/checkout",
            "/orders/my-orders",
            "/wallet",
            "/participate",
            "/my-entries",
            "/coupons/validate",
            "/payments/initiate",
            "/payments/verify-manual",
        )
    ):
        return "Customer"
    if any(
        k in path
        for k in (
            "/health",
            "/settings",
            "/banners",
            "/popups",
            "/categories",
            "/products",
            "/packages",
            "/payment-methods",
            "/lotteries/active",
        )
    ):
        return "Public"
    return "Authenticated"


def tag_to_folder_order(tag: str) -> str:
    """Give a clean numbered ordering to folders."""
    order_map = {
        "Authentication": "01. Authentication & Profile",
        "Admin - Dashboard": "02. Admin - Dashboard",
        "Admin - Users": "03. Admin - User Management",
        "Categories": "04. Categories",
        "Products": "05. Products & Dynamic Fields",
        "Packages": "06. Packages",
        "Coupons": "07. Coupons & Discounts",
        "Orders & Checkout": "08. Orders & Checkout",
        "Payment Methods": "09. Payment Methods",
        "Payments": "10. Payments & Webhooks",
        "Wallet & Top-Ups": "11. Wallet & Top-Ups",
        "Lottery & Lucky Spin": "12. Lottery & Lucky Spin",
        "Marketing (Banners & Popups)": "13. Marketing (Banners & Popups)",
        "Site Settings": "14. Site Settings",
        "Media": "15. Media Uploads",
        "Health": "16. System Health",
    }
    return order_map.get(tag, f"99. {tag}")


def build_postman_collection() -> Dict[str, Any]:
    openapi = app.openapi()
    components = openapi.get("components", {}).get("schemas", {})
    paths = openapi.get("paths", {})

    collection: Dict[str, Any] = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": "Digital Product Selling System API",
            "description": (
                "# Digital Product Selling System API Collection\n\n"
                "Complete API documentation and Postman workspace for the Digital Product Selling System "
                "(BoostGhor-like platform).\n\n"
                "### Features Included:\n"
                "- **Authentication**: Registration, Login, Custom Google OAuth, JWT Refresh, Password Reset\n"
                "- **Admin Management**: Dashboard Metrics, User Management, Role RBAC\n"
                "- **Catalog**: Categories, Products, Dynamic Customer Input Fields, Packages\n"
                "- **E-commerce**: Dynamic Checkout, Coupon Validation, Multi-order Tracking\n"
                "- **Payments**: Manual Gateway with TrxID Verification, bKash/Nagad Webhooks\n"
                "- **Wallet System**: Customer Balance, Top-Up Requests, Admin Approvals\n"
                "- **Lottery & Spins**: Ticket Purchases, Lucky Spin Draws, Prize Distribution\n"
                "- **Marketing & CMS**: Banners, Flash Popups, Public Site Settings, Media Uploads\n\n"
                "### Quick Setup:\n"
                "1. Run the server: `make dev` or `uv run uvicorn app.main:app --reload` (port 8000).\n"
                "2. Call `POST /api/v1/auth/admin/login` for Admin or `POST /api/v1/auth/google` for Customer.\n"
                "   The test script will **automatically store** `access_token` and `admin_token` into Postman variables!\n"
                "3. Subsequent authenticated endpoints automatically inherit the `{{access_token}}` variable."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string",
                "description": "Base URL of the running API server",
            },
            {
                "key": "access_token",
                "value": "",
                "type": "string",
                "description": "Bearer JWT Access Token (auto-updated upon login)",
            },
            {
                "key": "refresh_token",
                "value": "",
                "type": "string",
                "description": "Bearer JWT Refresh Token",
            },
            {
                "key": "admin_token",
                "value": "",
                "type": "string",
                "description": "Admin Bearer JWT Token for administrative operations",
            },
        ],
        "item": [],
    }

    folders: Dict[str, List[Dict[str, Any]]] = {}

    for path, path_item in sorted(paths.items()):
        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue

            tags = operation.get("tags", ["General"])
            tag = tags[0] if tags else "General"
            folder_name = tag_to_folder_order(tag)

            summary = operation.get("summary", f"{method.upper()} {path}")
            description = operation.get("description", "")
            role = determine_role(path, summary, description)

            # Build URL and path variables
            url_path_parts = [p for p in path.strip("/").split("/") if p]
            postman_path_parts: List[str] = []
            path_variables: List[Dict[str, Any]] = []

            for part in url_path_parts:
                if part.startswith("{") and part.endswith("}"):
                    var_name = part[1:-1]
                    postman_path_parts.append(f":{var_name}")
                    path_variables.append(
                        {
                            "key": var_name,
                            "value": "1",
                            "description": f"Target ID for {var_name}",
                        }
                    )
                else:
                    postman_path_parts.append(part)

            # Build Query parameters
            query_params: List[Dict[str, Any]] = []
            for param in operation.get("parameters", []):
                if param.get("in") == "query":
                    query_params.append(
                        {
                            "key": param["name"],
                            "value": str(param.get("schema", {}).get("default", "")),
                            "description": param.get("description", ""),
                            "disabled": not param.get("required", False),
                        }
                    )

            # Headers
            headers: List[Dict[str, str]] = []
            if "/payments/webhook/sms" in path:
                headers.append({
                    "key": "X-Device-Secret",
                    "value": "default-secure-sms-device-secret-key-change-in-prod",
                    "description": "Secret token configured on Android forwarding device",
                })

            # Request Body
            request_body: Optional[Dict[str, Any]] = None
            if "requestBody" in operation:
                rb = operation["requestBody"]
                content = rb.get("content", {})
                if "application/json" in content:
                    headers.append({"key": "Content-Type", "value": "application/json"})
                    if path in CUSTOM_EXAMPLES:
                        sample_payload = CUSTOM_EXAMPLES[path]
                    else:
                        schema = content["application/json"].get("schema", {})
                        sample_payload = generate_sample_from_schema(schema, components)
                    request_body = {
                        "mode": "raw",
                        "raw": json.dumps(sample_payload, indent=2),
                        "options": {"raw": {"language": "json"}},
                    }
                elif "multipart/form-data" in content:
                    request_body = {
                        "mode": "formdata",
                        "formdata": [
                            {
                                "key": "file",
                                "type": "file",
                                "src": "",
                                "description": "Select an image or document to upload",
                            }
                        ],
                    }

            # Auth configuration
            auth_config: Optional[Dict[str, Any]] = None
            if role == "Admin":
                auth_config = {
                    "type": "bearer",
                    "bearer": [
                        {
                            "key": "token",
                            "value": "{{access_token}}",
                            "type": "string",
                        }
                    ],
                }
            elif role == "Customer" or role == "Authenticated":
                auth_config = {
                    "type": "bearer",
                    "bearer": [
                        {
                            "key": "token",
                            "value": "{{access_token}}",
                            "type": "string",
                        }
                    ],
                }
            else:
                auth_config = {"type": "noauth"}

            # Markdown documentation for Postman description tab
            doc_lines = [
                f"### {summary}",
                f"**Access Role Required**: `{role}`\n",
            ]
            if description:
                doc_lines.append(f"{description}\n")

            if path_variables:
                doc_lines.append("#### Path Parameters:")
                for pv in path_variables:
                    doc_lines.append(f"- `{pv['key']}`: {pv['description']}")
                doc_lines.append("")

            if query_params:
                doc_lines.append("#### Query Parameters:")
                for qp in query_params:
                    doc_lines.append(
                        f"- `{qp['key']}` ({'Required' if not qp['disabled'] else 'Optional'}): {qp['description']}"
                    )
                doc_lines.append("")

            # Event / Test script
            events: List[Dict[str, Any]] = []
            if "/admin/login" in path:
                events.append(
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                "// Automatically save tokens to Collection Variables",
                                "if (pm.response.code === 200) {",
                                "    var jsonData = pm.response.json();",
                                "    if (jsonData.data && jsonData.data.access_token) {",
                                "        pm.collectionVariables.set('access_token', jsonData.data.access_token);",
                                "        pm.collectionVariables.set('admin_token', jsonData.data.access_token);",
                                "        console.log('✅ admin_token and access_token saved to Collection Variables');",
                                "    }",
                                "    if (jsonData.data && jsonData.data.refresh_token) {",
                                "        pm.collectionVariables.set('refresh_token', jsonData.data.refresh_token);",
                                "    }",
                                "}",
                            ],
                        },
                    }
                )
            elif "/auth/google" in path:
                events.append(
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                "// Automatically save tokens to Collection Variables",
                                "if (pm.response.code === 200 || pm.response.code === 201) {",
                                "    var jsonData = pm.response.json();",
                                "    if (jsonData.data && jsonData.data.access_token) {",
                                "        pm.collectionVariables.set('access_token', jsonData.data.access_token);",
                                "        console.log('✅ access_token saved to Collection Variables');",
                                "    }",
                                "    if (jsonData.data && jsonData.data.refresh_token) {",
                                "        pm.collectionVariables.set('refresh_token', jsonData.data.refresh_token);",
                                "    }",
                                "}",
                            ],
                        },
                    }
                )

            url_obj: Dict[str, Any] = {
                "raw": "{{base_url}}/" + "/".join(postman_path_parts),
                "host": ["{{base_url}}"],
                "path": postman_path_parts,
            }
            if path_variables:
                url_obj["variable"] = path_variables
            if query_params:
                url_obj["query"] = query_params

            postman_item: Dict[str, Any] = {
                "name": f"[{role}] {summary}",
                "request": {
                    "method": method.upper(),
                    "header": headers,
                    "url": url_obj,
                    "description": "\n".join(doc_lines),
                },
                "response": [],
            }

            if auth_config:
                postman_item["request"]["auth"] = auth_config
            if request_body:
                postman_item["request"]["body"] = request_body
            if events:
                postman_item["event"] = events

            folders.setdefault(folder_name, []).append(postman_item)

    # Convert sorted folders into collection items
    for folder_name in sorted(folders.keys()):
        collection["item"].append(
            {
                "name": folder_name,
                "item": folders[folder_name],
                "description": f"Endpoints related to {folder_name}",
            }
        )

    return collection


if __name__ == "__main__":
    collection_data = build_postman_collection()
    out_file = "Digital_Product_Selling_System.postman_collection.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(collection_data, f, indent=2, ensure_ascii=False)

    total_endpoints = sum(len(folder["item"]) for folder in collection_data["item"])
    print(f" Successfully generated Postman Collection: '{out_file}'")
    print(f" Total Folders: {len(collection_data['item'])}")
    print(f" Total Documented Endpoints: {total_endpoints}")
