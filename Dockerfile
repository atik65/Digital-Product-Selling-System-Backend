# ==========================================
# Stage 1: Build virtualenv using uv
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and use standard copy mode
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install production dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev


# ==========================================
# Stage 2: Production runtime image
# ==========================================
FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

# Ensure output is sent straight to terminal without buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Create a dedicated non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy installed virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application source code and migrations
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup main.py ./
COPY --chown=appuser:appgroup scripts ./scripts

# Create uploads directory and assign ownership
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app/uploads

# Switch to non-root user
USER appuser

# Expose default application port
EXPOSE 8000

# Apply database migrations on startup and launch Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
