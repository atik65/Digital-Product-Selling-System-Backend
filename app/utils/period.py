from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Tuple

# Day / month boundaries follow Bangladesh time (UTC+6, no daylight saving),
# so "this month" starts at 00:00 on the 1st in Dhaka, not in UTC.
BUSINESS_TZ = timezone(timedelta(hours=6))


def _now_business(now: Optional[datetime] = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(BUSINESS_TZ)


def business_date_start_utc(day: date) -> datetime:
    """Start (00:00 Dhaka) of the given calendar day, expressed in UTC."""
    return datetime.combine(day, time.min, tzinfo=BUSINESS_TZ).astimezone(timezone.utc)


def day_range_utc(now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """[start, end) of the current business day, in UTC."""
    today = _now_business(now).date()
    return business_date_start_utc(today), business_date_start_utc(
        today + timedelta(days=1)
    )


def month_range_utc(now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """[start, end) of the current business month (1st to 1st), in UTC."""
    today = _now_business(now).date()
    first = today.replace(day=1)
    next_first = (first + timedelta(days=32)).replace(day=1)
    return business_date_start_utc(first), business_date_start_utc(next_first)
