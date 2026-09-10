from slowapi import Limiter
from slowapi.util import get_remote_address

# Central IP-based rate limiter
# - default_limits: Applies to all routes unless overridden
# - headers_enabled: Adds X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    headers_enabled=True,
)
