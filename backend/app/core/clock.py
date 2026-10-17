"""Time helpers.

Home Assistant stores every timestamp as a *naive UTC* datetime. To keep that
contract explicit across the codebase:

- Use ``utc_now()`` for anything compared against database columns.
- Use ``ensure_utc()`` before returning timestamps from the API, so they are
  serialized with an explicit offset and browsers do not read them as local time.
- Use ``local_now()`` / ``to_local()`` for human-facing buckets (hour of the day,
  day of the week, month), in the timezone configured by ``settings.TIMEZONE``.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def utc_now() -> datetime:
    """Current time as a naive UTC datetime, comparable with HA columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_utc(value: datetime) -> datetime:
    """Attach UTC to naive datetimes coming from the database."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def local_tz() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE)


def local_now() -> datetime:
    """Current time in the school's timezone (aware)."""
    return datetime.now(local_tz())


def to_local(value: datetime) -> datetime:
    """Convert a database (naive UTC) or aware datetime to the school's timezone."""
    return ensure_utc(value).astimezone(local_tz())
