from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.db import get_db

router = APIRouter(prefix="/reservations", tags=["reservations"])


class ReservationCreate(BaseModel):
    performance_id: int
    platform: str = Field(..., max_length=50)
    reservation_number: Optional[str] = Field(default=None, max_length=128)
    name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=64)
    seat_info: Optional[str] = Field(default=None, max_length=256)
    quantity: int = Field(default=1, ge=0)
    status: Optional[models.ReservationStatus] = None


class ReservationResponse(BaseModel):
    id: int
    performance_id: int
    platform: str
    reservation_number: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    seat_info: Optional[str]
    quantity: int
    status: models.ReservationStatus
    token: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusUpdatePayload(BaseModel):
    status: models.ReservationStatus
    note: Optional[str] = None


class QRIssueResponse(BaseModel):
    token: str
    status: models.ReservationStatus
    issued_at: datetime

    class Config:
        from_attributes = True


BASE36_ALPHABET = string.digits + string.ascii_lowercase
TOKEN_LENGTH = 8


def _base36_encode(number: int) -> str:
    if number < 0:
        raise ValueError("Number must be positive")
    if number == 0:
        return "0"

    digits = []
    while number:
        number, remainder = divmod(number, 36)
        digits.append(BASE36_ALPHABET[remainder])
    return "".join(reversed(digits))


def _generate_base36_token() -> str:
    max_value = 36**TOKEN_LENGTH
    random_number = secrets.randbelow(max_value)
    return _base36_encode(random_number).zfill(TOKEN_LENGTH)


def _generate_unique_token(db: Session) -> str:
    while True:
        token = _generate_base36_token()
        exists = db.query(models.Reservation).filter_by(token=token).first()
        if not exists:
            return token


def _record_event(
    db: Session,
    reservation: models.Reservation,
    event_type: str,
    previous_status: Optional[models.ReservationStatus],
    new_status: Optional[models.ReservationStatus],
    payload: Optional[dict[str, Any]] = None,
) -> None:
    event = models.ReservationEvent(
        reservation_id=reservation.id,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        payload=payload,
    )
    db.add(event)


def _touch_updated_at(reservation: models.Reservation) -> None:
    reservation.updated_at = datetime.now(timezone.utc)


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)):
    reservation = models.Reservation(
        performance_id=payload.performance_id,
        platform=payload.platform,
        reservation_number=payload.reservation_number,
        name=payload.name,
        phone=payload.phone,
        seat_info=payload.seat_info,
        quantity=payload.quantity,
        status=payload.status or models.ReservationStatus.reserved_unassigned,
    )

    db.add(reservation)
    db.flush()
    _record_event(
        db,
        reservation,
        event_type="reservation_created",
        previous_status=None,
        new_status=reservation.status,
        payload=payload.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}/status", response_model=ReservationResponse)
def update_status(
    reservation_id: int,
    payload: StatusUpdatePayload,
    db: Session = Depends(get_db),
):
    reservation = db.get(models.Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    previous_status = reservation.status
    reservation.status = payload.status
    _touch_updated_at(reservation)
    _record_event(
        db,
        reservation,
        event_type="status_updated",
        previous_status=previous_status,
        new_status=payload.status,
        payload={"note": payload.note} if payload.note else None,
    )

    db.commit()
    db.refresh(reservation)
    return reservation


@router.post("/{reservation_id}/issue-qr", response_model=QRIssueResponse)
def issue_qr(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(models.Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.token is None:
        reservation.token = _generate_unique_token(db)

    previous_status = reservation.status
    reservation.status = models.ReservationStatus.issued
    _touch_updated_at(reservation)

    _record_event(
        db,
        reservation,
        event_type="qr_issued",
        previous_status=previous_status,
        new_status=reservation.status,
        payload={"token": reservation.token},
    )

    db.commit()
    db.refresh(reservation)

    return QRIssueResponse(
        token=reservation.token,
        status=reservation.status,
        issued_at=reservation.updated_at,
    )
