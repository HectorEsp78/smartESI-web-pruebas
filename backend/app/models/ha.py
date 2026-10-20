"""SQLAlchemy models of the Home Assistant recorder tables we read.

Only the columns the statistics module needs are mapped. This installation runs
an older Home Assistant schema: the ``states`` table still carries ``entity_id``
and naive-UTC ``datetime`` timestamps (no ``metadata_id`` / ``last_updated_ts``).

The application is **read-only**: these tables belong to Home Assistant and must
never be written to from here.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StatisticsMeta(Base):
    """Mapping for Home Assistant's ``statistics_meta`` table."""

    __tablename__ = "statistics_meta"

    id = Column(Integer, primary_key=True)
    statistic_id = Column(String, unique=True, index=True)
    source = Column(String)
    unit_of_measurement = Column(String)
    has_mean = Column(Boolean)
    has_sum = Column(Boolean)
    name = Column(String)


class State(Base):
    """Mapping for Home Assistant's ``states`` table."""

    __tablename__ = "states"

    state_id = Column(Integer, primary_key=True)
    domain = Column(String(64))
    entity_id = Column(String(255), index=True)
    state = Column(String(255))
    attributes = Column(String)
    event_id = Column(Integer)
    last_changed = Column(DateTime)
    last_updated = Column(DateTime)
    created = Column(DateTime)
    old_state_id = Column(Integer)


class Statistics(Base):
    """Mapping for Home Assistant's hourly ``statistics`` table."""

    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True)
    created = Column(DateTime)
    start = Column(DateTime, index=True)
    mean = Column(Float)
    min = Column(Float)
    max = Column(Float)
    last_reset = Column(DateTime)
    state = Column(Float)
    sum = Column(Float)
    metadata_id = Column(Integer, ForeignKey("statistics_meta.id"), index=True)
