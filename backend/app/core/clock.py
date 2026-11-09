"""Time helpers.

Home Assistant stores every timestamp as a *naive UTC* datetime. To keep that
contract explicit across the codebase:

- Use ``utc_now()`` for anything compared against database columns.
- Use ``to_utc_naive()`` to turn an aware datetime into a database bound.
- Use ``ensure_utc()`` before returning timestamps from the API, so they are
  serialized with an explicit offset and browsers do not read them as local time.
- Use ``local_now()`` / ``to_local()`` for human-facing buckets (hour of the day,
  day of the week, month), in the timezone configured by ``settings.TIMEZONE``.
- Use ``elapsed_hours()`` to measure aware datetimes: Python ignores DST when
  it subtracts two datetimes that share a ``tzinfo``.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

HOUR_SECONDS = 3600

# Dates outside this window are rejected with a clear message. Besides having no
# meaning for this data, the extremes of ``date`` overflow when they are shifted
# to another timezone or moved by a day.
MIN_QUERY_DATE = date(2000, 1, 1)
MAX_QUERY_DATE = date(2100, 12, 31)


def utc_now() -> datetime:
    """Current time as a naive UTC datetime, comparable with HA columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_utc(value: datetime) -> datetime:
    """Attach UTC to naive datetimes coming from the database."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_utc_naive(value: datetime) -> datetime:
    """Convert an aware datetime to the naive UTC format of the HA columns."""
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def local_tz() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE)


def local_now() -> datetime:
    """Current time in the school's timezone (aware)."""
    return datetime.now(local_tz())


def to_local(value: datetime) -> datetime:
    """Convert a database (naive UTC) or aware datetime to the school's timezone."""
    return ensure_utc(value).astimezone(local_tz())


def floor_hour_epoch(value_utc_naive: datetime) -> int:
    """Epoch seconds of the UTC hour containing a naive UTC datetime."""
    seconds = int(value_utc_naive.replace(tzinfo=timezone.utc).timestamp())
    return seconds // HOUR_SECONDS * HOUR_SECONDS


def local_hour_from_epoch(epoch_seconds: int) -> datetime:
    """Local-aware hour containing the given epoch."""
    moment = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    return moment.astimezone(local_tz()).replace(minute=0, second=0, microsecond=0)


def local_hour_from_utc(value_utc_naive: datetime) -> datetime:
    """Local-aware hour containing a naive UTC datetime."""
    return local_hour_from_epoch(floor_hour_epoch(value_utc_naive))


def elapsed_hours(start: datetime, end: datetime) -> float:
    """Real hours between two aware datetimes, including DST changes."""
    return (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() / 3600.0


def validate_query_dates(*values: date) -> None:
    """Raise ``ValueError`` when a requested date is outside the supported window."""
    if any(value < MIN_QUERY_DATE or value > MAX_QUERY_DATE for value in values):
        raise ValueError(
            f"Las fechas deben estar entre {MIN_QUERY_DATE.isoformat()} "
            f"y {MAX_QUERY_DATE.isoformat()}."
        )
