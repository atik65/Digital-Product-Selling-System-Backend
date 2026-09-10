# Configration regarding Open API Documentation (Swagger)
# /docs

from app.core.config import settings

TAGS_METADATA = [
    {
        "name": "Products",
        "description": "Operations with products like CRUD, filtering and stock management.",
        "externalDocs": {
            "description": "More product docs",
            "url": "https://example.com/docs/products",
        },
    },
]

API_DESCRIPTION = """
## Digital Product Selling System API
This API enables managing and selling digital products:
* **Authentication & RBAC**: Secure JWT tokens with User & Admin roles.
* **Product Catalog**: Digital products management, filtering, and categories.
* **Media & File Storage**: Upload and manage digital assets & thumbnails.
* **Health & Monitoring**: Database health, latency logging, and rate limiting.
"""

SWAGGER_UI_PARAMETERS = {
    "defaultModelsExpandDepth": -1,  # Schemas সেকশন হাইড রাখবে
    "syntaxHighlight.theme": "monokai",
    "persistAuthorization": True,  # টোকেন সেভ রাখবে
    "docExpansion": "list",
}

# পুরো কনফিগারেশন একটি ডিকশনারিতে প্যাক করা:
openapi_config = {
    "title": settings.PROJECT_NAME,
    "description": API_DESCRIPTION,
    "version": settings.VERSION,
    "debug": settings.DEBUG,
    "contact": {
        "name": "Atik",
        "email": "atik@gmail.com",
    },
    "openapi_tags": TAGS_METADATA,
    "swagger_ui_parameters": SWAGGER_UI_PARAMETERS,
}
