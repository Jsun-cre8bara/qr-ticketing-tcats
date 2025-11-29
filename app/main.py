from __future__ import annotations

from fastapi import FastAPI
from app.routers import reservations

app = FastAPI(title="QR Ticketing API", version="0.1.0")

app.include_router(reservations.router)

# 루트 엔드포인트
@app.get("/")
def root():
    return {
        "message": "QR Ticketing API is running!",
        "docs": "/docs"
    }

# 헬스체크
@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
