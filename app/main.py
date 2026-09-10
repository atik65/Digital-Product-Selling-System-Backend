from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import product, media, health, auth
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.core.middleware import TimeLoggerMiddleware
from app.core.swagger import openapi_config

# Initialize application-wide logging
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

app = FastAPI(**openapi_config)

# 1. State configuration for rate limiter
app.state.limiter = limiter

# 2. Register global exception handlers (including 429 RateLimitExceeded)
register_exception_handlers(app)

# 3. SlowAPI Rate Limiting Middleware
app.add_middleware(SlowAPIMiddleware)

# 4. CORS Middleware Setup
# Allows frontend frameworks (Next.js, Vite/React, Vue, mobile apps) to make cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Custom Time Logger Middleware
app.add_middleware(TimeLoggerMiddleware)

# 6. Include API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(product.router)
app.include_router(media.router)


# 7. Ensure uploads directory exists and mount static media files
Path("uploads").mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory="uploads"), name="media")
