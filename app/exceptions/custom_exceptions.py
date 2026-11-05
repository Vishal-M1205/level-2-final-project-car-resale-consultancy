from fastapi import status


class AppException(Exception):
    """Base application exception for all domain and HTTP errors."""

    def __init__(
        self,
        detail: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class BadRequestException(AppException):
    """Raised when request payload or business constraint is invalid (400)."""

    def __init__(self, detail: str = "Bad Request"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(AppException):
    """Raised when authentication fails or credentials are invalid (401)."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class SignatureError(UnauthorizedException):
    """Raised specifically when a JWT signature verification fails (401)."""

    def __init__(self, detail: str = "Invalid token signature"):
        super().__init__(detail=detail)


class InvalidSignatureException(SignatureError):
    """Alias for SignatureError."""

    pass


class TokenExpiredException(UnauthorizedException):
    """Raised when a JWT has expired (401)."""

    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail=detail)


class InvalidTokenException(UnauthorizedException):
    """Raised when a JWT is malformed or invalid (401)."""

    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail=detail)


class ForbiddenException(AppException):
    """Raised when user lacks permission to perform the requested action (403)."""

    def __init__(self, detail: str = "Forbidden: Not enough permissions"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(AppException):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Raised when an operation conflicts with existing state (409)."""

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)

