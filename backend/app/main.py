from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import AppError, app_error_handler
from app.api.v1 import candidates, extraction, gap_analysis, positions, recommendations

app = FastAPI(
    title="TalentMatch AI",
    description="AI-powered talent intelligence platform for software engineering roles.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


app.include_router(candidates.router, prefix="/api/v1")
app.include_router(positions.router, prefix="/api/v1")
app.include_router(extraction.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(gap_analysis.router, prefix="/api/v1")
