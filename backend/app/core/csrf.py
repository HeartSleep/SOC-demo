"""
CSRF Protection
Provides Cross-Site Request Forgery protection using itsdangerous
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.core.config import settings
from app.core.logging import get_logger
from typing import Optional
import secrets

logger = get_logger(__name__)

# Initialize serializer for CSRF tokens
csrf_serializer = URLSafeTimedSerializer(
    settings.CSRF_SECRET_KEY,
    salt="csrf-token"
)


def generate_csrf_token() -> str:
    """
    Generate a new CSRF token.

    Returns:
        str: CSRF token
    """
    # Generate random data
    random_data = secrets.token_urlsafe(32)

    # Sign the token
    token = csrf_serializer.dumps(random_data)

    return token


def verify_csrf_token(token: str, max_age: int = None) -> bool:
    """
    Verify a CSRF token.

    Args:
        token: CSRF token to verify
        max_age: Maximum age in seconds (default from settings)

    Returns:
        bool: True if valid, False otherwise
    """
    if max_age is None:
        max_age = settings.CSRF_TOKEN_EXPIRE_MINUTES * 60

    try:
        csrf_serializer.loads(token, max_age=max_age)
        return True
    except (SignatureExpired, BadSignature) as e:
        logger.warning(f"Invalid CSRF token: {e}")
        return False


async def csrf_protect(request: Request) -> None:
    """
    Middleware function to protect against CSRF attacks.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If CSRF token is missing or invalid
    """
    # Skip CSRF check for safe methods
    if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
        return

    # Skip CSRF check for API endpoints using Bearer tokens
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return

    # Get CSRF token from header
    csrf_token = request.headers.get("X-CSRF-Token")

    # Note: We don't support form-based CSRF tokens to avoid consuming request body
    # All API endpoints must include X-CSRF-Token header

    if not csrf_token:
        logger.warning(f"CSRF token missing for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing"
        )

    if not verify_csrf_token(csrf_token):
        logger.warning(f"Invalid CSRF token for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )


class CSRFProtectMiddleware:
    """
    CSRF Protection Middleware for FastAPI
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Paths to exclude from CSRF protection
        excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",  # Login doesn't need CSRF initially
        ]

        # Check if path should be excluded
        path = request.url.path
        if any(path.startswith(excluded) for excluded in excluded_paths):
            await self.app(scope, receive, send)
            return

        # Verify CSRF token
        try:
            await csrf_protect(request)
        except HTTPException as e:
            response = JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def get_csrf_token_header() -> dict:
    """
    Generate a new CSRF token and return it as a header.

    Returns:
        dict: Headers containing CSRF token
    """
    token = generate_csrf_token()
    return {"X-CSRF-Token": token}


def csrf_cookie_setter(response: JSONResponse) -> JSONResponse:
    """
    Set CSRF token in cookie.

    Args:
        response: FastAPI response object

    Returns:
        Response with CSRF cookie set
    """
    token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=True,
        secure=not settings.DEBUG,  # Only use secure in production
        samesite="strict",
        max_age=settings.CSRF_TOKEN_EXPIRE_MINUTES * 60
    )
    # Also add to headers for easier access
    response.headers["X-CSRF-Token"] = token
    return response