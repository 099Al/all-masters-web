import logging.config
import os

LOG_FILE = 'logs/web.log'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s - %(asctime)s - %(name)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'default',
            'filename': LOG_FILE,
            'mode': 'a',
            'encoding': 'utf8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['file', 'console'],
    },
}


logging.config.dictConfig(LOGGING_CONFIG)
