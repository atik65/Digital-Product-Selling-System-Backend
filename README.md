# Digital Product Selling System

A production-ready REST API for a Digital Product Selling System built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, and Docker Compose. This system follows a clean, layered architecture separating routing, business logic, data access, and database models.

---

## Architecture

This project is organized using a layered design pattern to ensure maintainability, testability, and separation of concerns:

- **Routes (`app/api/routes`)**: Handle incoming HTTP requests, input validation via dependencies, and response formatting. They delegate all business logic to services.
- **Services (`app/services`)**: Encapsulate the core business logic, orchestrate calls between different repositories, and enforce business rules.
- **Repositories (`app/repositories`)**: Manage data persistence and abstract all SQLAlchemy database queries away from business logic.
- **Models (`app/models`)**: Define database tables and relationships using SQLAlchemy Declarative Base.
- **Schemas (`app/schemas`)**: Pydantic models for request body validation, query parameter parsing, and response serialization.
- **Core (`app/core`)**: Central configuration, database session management, authentication utilities, custom middleware, and global exception handlers.

---

### Key Features

- 🏗️ **Clean Layered Architecture**: Strict separation of concerns (Routes → Services → Repositories → Models → Schemas).
- 🐳 **Production-Grade Dockerization**: Ultra-fast multi-stage `Dockerfile` powered by `uv`, non-root security user, automated startup migrations, and full-stack `docker-compose.yml`.
- 🔐 **JWT Authentication & RBAC**: Access & refresh tokens, password hashing with bcrypt, and flexible Role-Based Access Control (`require_role("admin")` or `require_role(["admin", "user"])`).
- 🆔 **Distributed Tracing & Request-ID**: Automatic `X-Request-ID` generation/propagation across headers, logs, and error responses.
- 📊 **Structured Logging**: Switch seamlessly between human-readable dev logs and single-line JSON logs (`LOG_FORMAT=json`) for Datadog/ELK/CloudWatch.
- 🛡️ **BaseAuditModel & Soft Delete**: Auto-managed `created_at`, `updated_at`, `is_deleted`, and `deleted_at` with safe `soft_delete()` and `restore()` methods to maintain referential integrity.
- 🌱 **Database Seeder (`make seed`)**: One-command population of Super Admin, regular user, and 8 sample products for instant out-of-the-box API testing.
- 🗄️ **PostgreSQL 16 & Alembic**: Complete migration environment with autogenerate detection and persistent Docker storage.
- ⏱️ **Rate Limiting**: Built-in request throttling powered by SlowAPI, preventing DDoS and brute-force attempts with standardized HTTP 429 errors.
- 📁 **Media Upload & Static Serving**: Image uploads with MIME validation, served statically under `/media`.
- 📦 **Standardized API Envelope**: Uniform JSON responses for success and error scenarios.
- ⚡ **Ultra-Fast Tooling & DX**: Instant dependency resolution with Astral's `uv`, linting/formatting with Ruff, and cross-platform `Makefile`.
- 🧪 **Comprehensive Automated Testing**: 26 unit tests covering auth, CRUD, seeding, soft deletes, and distributed tracing with isolated in-memory SQLite.

---

## Prerequisites

Before running this project, ensure you have the following installed:

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) (recommended package installer and resolver)
- [Docker](https://www.docker.com/) and Docker Compose
- `make` (optional, for running workflow shortcuts)

---

## Project Structure

```text
.
|-- alembic/
|   |-- versions/            # Database migration revisions
|   `-- env.py               # Alembic runtime configuration
|-- app/
|   |-- api/
|   |   `-- routes/          # API route definitions (auth, product, media, health)
|   |-- core/
|   |   |-- config.py        # Centralized settings and environment variables
|   |   |-- database.py      # SQLAlchemy engine, session factory, and Base
|   |   |-- exceptions.py    # Global exception handlers with request_id
|   |   |-- limiter.py       # Rate limiter configuration
|   |   |-- logging.py       # Request-ID ContextVar, filter, and JSON formatter
|   |   |-- middleware.py    # Request-ID propagation and performance timing
|   |   |-- security.py      # JWT authentication, bcrypt, and RBAC require_role
|   |   `-- swagger.py       # OpenAPI and Swagger UI custom configuration
|   |-- enums/               # Application-level enumerations
|   |-- models/
|   |   |-- base.py          # BaseAuditModel (timestamps, soft delete, restore)
|   |   |-- product.py       # Product database model
|   |   `-- user.py          # User database model
|   |-- repositories/        # Database queries and persistence layer
|   |-- schemas/             # Pydantic validation and serialization schemas
|   |-- services/            # Core business logic layer
|   `-- utils/               # Reusable utility functions (e.g. pagination)
|-- scripts/
|   `-- seed.py              # Idempotent database seeder (admin, user, products)
|-- tests/                   # Automated test suite (in-memory SQLite, 26 tests)
|   |-- conftest.py          # Pytest fixtures and mock client configuration
|   |-- test_audit_and_soft_delete.py # Timestamps and soft-delete tests
|   |-- test_auth.py         # Authentication and registration tests
|   |-- test_health.py       # Health check tests
|   |-- test_logging_and_tracing.py # Correlation ID and JSON logger tests
|   |-- test_products.py     # Product CRUD and RBAC permission tests
|   `-- test_seed.py         # Database seeding idempotency tests
|-- uploads/                 # Local directory for uploaded media files
|-- .dockerignore            # Files excluded from Docker builds
|-- .env.example             # Example environment configuration
|-- Dockerfile               # Multi-stage production-ready container build
|-- docker-compose.yml       # Stack definition (App + PostgreSQL)
|-- Makefile                 # Development task runner
|-- pyproject.toml           # Project dependencies and tool configurations
`-- README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd fastapi-template
```

### 2. Configure environment variables

Copy the example environment file and customize it if needed:

```bash
cp .env.example .env
```

### 3. Quick Start with Make

If you have `make` installed, you can run the entire initial setup in one command:

```bash
make setup
make dev
```

The `make setup` command will install dependencies with `uv sync`, launch the PostgreSQL container, and apply all pending database migrations.

---

## Manual Setup (Without Make)

If you prefer running commands directly without `make`:

### 1. Install dependencies

```bash
uv sync
```

### 2. Start PostgreSQL container

```bash
docker compose up -d --wait db
```

### 3. Apply database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the development server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## Running with Full Docker (Production Mode)

If you or your team want to run the entire stack (FastAPI application + PostgreSQL database) fully containerized inside Docker without needing Python or `uv` installed on the host machine:

### 1. Start the entire application stack
```bash
make docker-up
```
*(Or without Make: `docker compose up -d --build`)*

This command automatically:
1. Builds the lightweight, multi-stage FastAPI Docker image using `uv`.
2. Starts the PostgreSQL container and waits until the health check passes.
3. Automatically applies all pending Alembic database migrations (`alembic upgrade head`).
4. Launches the FastAPI app via Uvicorn on `http://127.0.0.1:8000`.

### 2. View live application logs
```bash
make docker-logs
```
*(Or without Make: `docker compose logs -f api`)*

### 3. Stop the Docker stack
```bash
make docker-down
```
*(Or without Make: `docker compose down`)*

> [!TIP]
> **Workflow Best Practice:**
> - **Local Development:** Run `make db-up` (only PostgreSQL in Docker) and `make dev` (FastAPI with instant hot-reload via `uv`).
> - **Testing / Production Deployment:** Run `make docker-up` to ensure the application runs smoothly in an isolated, containerized environment.

---

## Environment Variables

All settings are managed in `app/core/config.py` via Pydantic Settings and loaded from the `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `password` | PostgreSQL password |
| `DB_HOST` | `localhost` | Database host address |
| `DB_PORT` | `5433` | Host port mapped to PostgreSQL in `docker-compose.yml` |
| `DB_NAME` | `digital_product_db` | Database name |
| `JWT_SECRET_KEY` | *(sample key)* | Secret key used to sign and verify JWT tokens |
| `JWT_ALGORITHM` | `HS256` | Algorithm used for token signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifespan in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifespan in days |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | `console` | Log format: `console` (human-readable dev logs) or `json` (production structured logs) |

---

## Structured Logging & Request Tracing (Correlation ID)

Every HTTP request is assigned a unique **`X-Request-ID`** (Correlation ID):
- If the incoming client or API gateway sends an `X-Request-ID` header, the system retains and propagates it.
- If not provided, a unique UUID4 is automatically generated.
- The `X-Request-ID` is returned in all response headers and embedded in every error payload.
- Every internal log message automatically includes the `[request_id]` for instant distributed tracing.

### Switching Log Format
In `.env` or production environment:
```env
LOG_FORMAT=json
```
Produces single-line structured JSON logs with HTTP metadata (`method`, `path`, `status_code`, `process_time`, `client_ip`) ready for tools like Datadog, ELK Stack, and Grafana Loki.

---

## Makefile Commands

The included `Makefile` works across PowerShell, Git Bash, macOS, and Linux:

| Target | Description |
| :--- | :--- |
| `make help` | Show available targets and descriptions |
| `make setup` | Install dependencies, start PostgreSQL, and apply migrations |
| `make dev` | Start development server with hot-reload enabled |
| `make db-up` | Start PostgreSQL container and run pending migrations |
| `make db-down` | Stop PostgreSQL container |
| `make db-reset` | Stop container, wipe data volume, recreate container, and reapply migrations |
| `make seed` | Populate database with default admin, user, and 8 sample products |
| `make docker-build` | Build Docker images for the application stack |
| `make docker-up` | Start entire stack (DB + API) inside Docker |
| `make docker-down` | Stop all running Docker containers |
| `make docker-logs` | Follow logs from the Dockerized API container |
| `make migration m="msg"` | Generate an autogenerated Alembic migration revision |
| `make migrate` | Apply all pending migrations (`alembic upgrade head`) |
| `make rollback` | Revert the most recent migration revision (`alembic downgrade -1`) |
| `make migrate-status` | Display the current database revision |
| `make lint` | Check code quality using Ruff linter |
| `make format` | Auto-format codebase using Ruff formatter |
| `make test` | Run test suite using Pytest |

---

## Database Seeding

To quickly populate the database with initial users and sample products for immediate testing:

```bash
make seed
```

### Pre-configured Seed Accounts
| Account | Email | Password | Role |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@example.com` | `admin123` | `admin` |
| **Regular User** | `user@example.com` | `user123` | `user` |

> [!NOTE]
> The seeding script is **idempotent**. You can safely run `make seed` multiple times without generating duplicate record errors.

---

## API Documentation and Endpoints

Once the application is running, visit the interactive API documentation:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Default Endpoints

- **Health**:
  - `GET /health` - Service and database connectivity health check
- **Authentication**:
  - `POST /auth/register` - Register a new user account
  - `POST /auth/login` - Authenticate user and receive access + refresh tokens
  - `POST /auth/refresh` - Exchange a refresh token for a new access token
  - `GET /auth/me` - Retrieve authenticated user profile
- **Products (CRUD Reference)**:
  - `GET /products` - List products with pagination, sorting, and search
  - `POST /products` - Create a product
  - `GET /products/{id}` - Get product details
  - `PUT /products/{id}` - Update a product
  - `DELETE /products/{id}` - Delete a product
- **Media Upload**:
  - `POST /media/upload` - Upload an image file (PNG, JPG, JPEG, WEBP)
  - `GET /media/{filename}` - Serve uploaded static media

---

## Database Migrations Workflow

1. Modify or add models inside `app/models/`.
2. Ensure new models are imported in `alembic/env.py` so Alembic can detect them.
3. Generate a migration revision:
   ```bash
   make migration m="add new table"
   # or: uv run alembic revision --autogenerate -m "add new table"
   ```
4. Review the generated script in `alembic/versions/`.
5. Apply the migration:
   ```bash
   make migrate
   # or: uv run alembic upgrade head
   ```

---

## Extending the Template

To add a new feature or resource (for example, `Order`), follow these steps:

1. **Model (`app/models/order.py`)**: Create the SQLAlchemy model inheriting from `Base`.
2. **Schemas (`app/schemas/order.py`)**: Create Pydantic schemas for request creation, update, and response serialization.
3. **Repository (`app/repositories/order_repository.py`)**: Implement data access methods (queries, filters, commits) taking a SQLAlchemy `Session`.
4. **Service (`app/services/order_service.py`)**: Implement business logic, validation rules, and coordinate repository calls.
5. **Route (`app/api/routes/order.py`)**: Define API endpoints, inject `db` session, and call the service.
6. **Register**: Import and mount the router in `app/main.py`:
   ```python
   from app.api.routes import order

   app.include_router(order.router)
   ```
7. **Migrate**: Run `make migration m="create orders table"` and `make migrate`.

---

## Code Quality and Testing

### Linting and Formatting

Code quality is enforced using Ruff:

```bash
# Run linter
make lint

# Automatically format code
make format
```

### Automated Testing

Automated tests run using Pytest with an isolated, in-memory SQLite database (`sqlite:///:memory:`). Tests run in milliseconds and will not alter or delete your development PostgreSQL database:

```bash
# Run the test suite
make test

# Run tests with verbose output
uv run pytest -v
```
