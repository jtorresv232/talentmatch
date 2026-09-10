from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, detail: str, code: str, status_code: int = 400):
        self.detail = detail
        self.code = code
        self.status_code = status_code


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


def not_found(entity: str, entity_id: str) -> AppError:
    return AppError(
        detail=f"{entity} {entity_id} not found",
        code=f"{entity.lower()}_not_found",
        status_code=404,
    )
