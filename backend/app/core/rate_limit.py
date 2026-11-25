import time
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from app.core.config import settings


class AuthRateLimiter:
    """
    Thread-safe sliding-window rate limiter for sensitive authentication endpoints
    to prevent brute-force credential stuffing and denial of service.
    """
    def __init__(self, limit: int = 10, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def check(self, request: Request, endpoint: str = "auth"):
        # Allow disabling or high threshold in test mode
        if settings.ENVIRONMENT == "test":
            return

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        key = f"{client_ip}:{endpoint}"
        with self.lock:
            # Purge expired timestamps outside current window
            self.requests[key] = [t for t in self.requests[key] if now - t < self.window_seconds]
            if len(self.requests[key]) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many {endpoint} attempts from this IP. Rate limit exceeded. Try again in {self.window_seconds}s."
                )
            self.requests[key].append(now)

    def reset(self):
        with self.lock:
            self.requests.clear()

    def is_allowed(self, client_ip: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        now = time.time()
        key = f"{client_ip}:test"
        with self.lock:
            self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
            if len(self.requests[key]) >= max_requests:
                return False
            self.requests[key].append(now)
            return True


auth_rate_limiter = AuthRateLimiter(limit=settings.AUTH_RATE_LIMIT_PER_MINUTE)
