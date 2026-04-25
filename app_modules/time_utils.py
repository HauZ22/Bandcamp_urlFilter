import os
from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_APP_TIMEZONE = "UTC"
APP_TIMEZONE_ENV_VAR = "APP_TIMEZONE"


def get_app_timezone_name() -> str:
    configured = str(os.getenv(APP_TIMEZONE_ENV_VAR, "")).strip()
    return configured or DEFAULT_APP_TIMEZONE


def get_app_timezone() -> tzinfo:
    timezone_name = get_app_timezone_name()
    if timezone_name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def get_app_now() -> datetime:
    return datetime.now(get_app_timezone())


def to_app_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(get_app_timezone())


def format_app_datetime(value: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return to_app_timezone(value).strftime(fmt)
