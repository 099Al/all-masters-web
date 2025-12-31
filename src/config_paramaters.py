from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field



@dataclass
class Configs:
    UTC_PLUS_5: timezone = timezone(timedelta(hours=5))
    EDIT_REQUEST_LIMIT: int = 4
    SIMILARITY_THRESHOLD: float = 0.4
    MESSAGES_TO_SPECIALISTS_LIMIT = 100
    PAGINATION_PER_PAGE = 5

configs = Configs()