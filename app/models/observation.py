from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Observation:
    border_id: str
    border_name: str

    # US -> Canada (CBP)
    uscan_passenger_lanes: int | None = None
    uscan_passenger_delay: int | None = None
    uscan_commercial_lanes: int | None = None
    uscan_commercial_delay: int | None = None
    uscan_updated: datetime | None = None

    # Canada -> US (CBSA)
    canus_passenger_lanes: int | None = None
    canus_passenger_delay: int | None = None
    canus_commercial_lanes: int | None = None
    canus_commercial_delay: int | None = None
    canus_updated: datetime | None = None

    # When our application created this observation
    observation_time: datetime | None = None

    def __post_init__(self):
        self.uscan_updated = to_utc(self.uscan_updated)
        self.canus_updated = to_utc(self.canus_updated)
        self.observation_time = to_utc(self.observation_time)


def to_utc(value: datetime | None) -> datetime | None:
    """
    Convert a datetime to UTC.

    Naive datetimes are assumed to already be UTC.
    Timezone-aware datetimes are converted to UTC.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
