from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Declarative SQLAlchemy base class."""


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    reserved_unassigned = "reserved_unassigned"
    reserved_assigned = "reserved_assigned"
    issued = "issued"
    checked_in = "checked_in"
    cancelled = "cancelled"
    expired = "expired"


reservation_status_enum = ENUM(
    ReservationStatus,
    name="reservation_status",
    create_type=False,
    validate_strings=True,
)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    performance_id: Mapped[int] = mapped_column(nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    reservation_number: Mapped[Optional[str]] = mapped_column(String(128))
    name: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    seat_info: Mapped[Optional[str]] = mapped_column(String(256))
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        reservation_status_enum,
        nullable=False,
        server_default=ReservationStatus.reserved_unassigned.value,
    )
    token: Mapped[Optional[str]] = mapped_column(String(16), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    seat_statuses: Mapped[list["SeatStatus"]] = relationship(
        back_populates="reservation", cascade="all, delete-orphan"
    )
    events: Mapped[list["ReservationEvent"]] = relationship(
        back_populates="reservation", cascade="all, delete-orphan"
    )


class SeatStatus(Base):
    __tablename__ = "seat_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reservations.id"))
    seat_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    note: Mapped[Optional[str]] = mapped_column(Text())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    reservation: Mapped[Optional[Reservation]] = relationship(back_populates="seat_statuses")


class ReservationEvent(Base):
    __tablename__ = "reservation_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_status: Mapped[Optional[ReservationStatus]] = mapped_column(
        reservation_status_enum
    )
    new_status: Mapped[Optional[ReservationStatus]] = mapped_column(
        reservation_status_enum
    )
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reservation: Mapped[Reservation] = relationship(back_populates="events")
