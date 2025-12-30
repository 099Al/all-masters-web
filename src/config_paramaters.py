from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

UTC_PLUS_5 = timezone(timedelta(hours=5))

EDIT_REQUEST_LIMIT = 4    # per hour

SIMILARITY_THRESHOLD = 0.4


@dataclass
class Configs:
    UTC_PLUS_5: timezone = timezone(timedelta(hours=5))
    EDIT_REQUEST_LIMIT: int = 4
    SIMILARITY_THRESHOLD: float = 0.4

configs = Configs()