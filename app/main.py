from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import (
    health,
    auth,
    users,
    categories,
    products,
    packages,
    coupons,
    orders,
    payment_methods,
    payments,
    wallet,
    lottery,
    marketing,
    settings as settings_route,
    dashboard,
    media,
)
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

# 2. Register global exception handlers
register_exception_handlers(app)

# 3. SlowAPI Rate Limiting Middleware
app.add_middleware(SlowAPIMiddleware)

# 4. CORS Middleware Setup
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

# 6. Include API Routers (/api/v1 and root)
api_v1_router = APIRouter(prefix="/api/v1")
all_routers = [
    health.router,
    auth.router,
    users.router,
    categories.router,
    products.router,
    packages.router,
    coupons.router,
    orders.router,
    payment_methods.router,
    payments.router,
    wallet.router,
    lottery.router,
    marketing.router,
    settings_route.router,
    dashboard.router,
    media.router,
]

for router in all_routers:
    api_v1_router.include_router(router)

app.include_router(api_v1_router)

# Root-level health check for container orchestrators
app.include_router(health.router)

# 7. Ensure uploads directory exists and mount static media files
Path("uploads").mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory="uploads"), name="media")
