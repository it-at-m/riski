from http import HTTPStatus
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _is_oparl_path(path: str) -> bool:
    return path.startswith("/api/oparl/")


def _build_oparl_error(*, status_code: int, message: str, details: Any | None = None) -> dict[str, Any]:
    title = HTTPStatus(status_code).phrase if status_code in HTTPStatus._value2member_map_ else "Error"
    payload: dict[str, Any] = {
        "type": "https://schema.oparl.org/1.1/Error",
        "title": title,
        "status": status_code,
        "message": message,
    }
    if details is not None:
        payload["details"] = details
    return payload


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if not _is_oparl_path(request.url.path):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

    if isinstance(exc.detail, dict):
        message = str(exc.detail.get("message", "Request failed"))
        details = exc.detail.get("details")
    else:
        message = str(exc.detail) if exc.detail is not None else "Request failed"
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_oparl_error(status_code=exc.status_code, message=message, details=details),
        headers=exc.headers,
    )


def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    if not _is_oparl_path(request.url.path):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    return JSONResponse(
        status_code=422,
        content=_build_oparl_error(
            status_code=422,
            message="Request validation failed",
            details=exc.errors(),
        ),
    )
