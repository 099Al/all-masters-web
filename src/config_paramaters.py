from datetime import datetime, timedelta, timezone


UTC_PLUS_5 = timezone(timedelta(hours=5))

EDIT_REQUEST_LIMIT = 4    # per hour

SIMILARITY_THRESHOLD = 0.4



MESSAGES_TO_SPECIALISTS_LIMIT = 3