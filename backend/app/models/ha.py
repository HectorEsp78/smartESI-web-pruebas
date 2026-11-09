"""SQLAlchemy models of the Home Assistant recorder tables we read.

Only the columns the statistics module needs are mapped. This installation runs
an older Home Assistant schema: the ``states`` table still carries ``entity_id``
and naive-UTC ``datetime`` timestamps (no ``metadata_id`` / ``last_updated_ts``).

The application is **read-only**: these tables belong to Home Assistant and must
never be written to from here.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class StatisticsMeta(Base):
    """Mapping for Home Assistant's ``statistics_meta`` table."""

    __tablename__ = "statistics_meta"

    id: Mapped[int] = mapped_column(primary_key=True)
    statistic_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[str | None] = mapped_column(String(32))
    unit_of_measurement: Mapped[str | None] = mapped_column(String(255))
    has_mean: Mapped[bool | None]
    has_sum: Mapped[bool | None]
    name: Mapped[str | None] = mapped_column(String(255))


class State(Base):
    """Mapping for Home Assistant's ``states`` table."""

    __tablename__ = "states"

    state_id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(255), index=True)
    state: Mapped[str] = mapped_column(String(255))
    attributes: Mapped[str | None] = mapped_column(String)
    event_id: Mapped[int | None]
    last_changed: Mapped[datetime | None]
    last_updated: Mapped[datetime]
    created: Mapped[datetime | None]
    old_state_id: Mapped[int | None]


class Statistics(Base):
    """Mapping for Home Assistant's hourly ``statistics`` table."""

    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime | None]
    start: Mapped[datetime] = mapped_column(index=True)
    mean: Mapped[float | None]
    min: Mapped[float | None]
    max: Mapped[float | None]
    last_reset: Mapped[datetime | None]
    state: Mapped[float | None]
    sum: Mapped[float | None]
    metadata_id: Mapped[int] = mapped_column(ForeignKey("statistics_meta.id"), index=True)
