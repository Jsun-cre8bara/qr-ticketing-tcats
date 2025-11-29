from __future__ import annotations

from fastapi import FastAPI

from app.routers import reservations

app = FastAPI(title="QR Ticketing API", version="0.1.0")

app.include_router(reservations.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
