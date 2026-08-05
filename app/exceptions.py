from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail


class LinkNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Link not found or expired"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
