import logging.config
import os
import tempfile

from version import __version__, __version_info__

APP_VERSION = __version__
MAJOR_VERSION = __version_info__[0]
MINOR_VERSION = __version_info__[1]

RELEASE_STAGE = os.getenv('RELEASE_STAGE')

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(ROOT_PATH)

# Use this timezone as default for timezone unaware dates
TIMEZONE = 'Europe/Amsterdam'

default_handlers = ['default']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Existing loggers are 'disabled' below
    'formatters': {
        'basic': {
            'format': '[%(module)s] %(levelname)s %(message)s'
        },
        'advanced': {
            'format': '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'advanced'
        }
    },
    'loggers': {
        'ocd_frontend': {
            'handlers': default_handlers,
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': default_handlers,
        'level': 'WARNING',
        'propagate': False
    },
}

# Configure python logging system with LOGGING dict
logging.config.dictConfig(LOGGING)

# The path of the directory used to store static files
DATA_DIR_PATH = os.path.join(PROJECT_PATH, 'data')

# The path of the directory used to store temporary files
TEMP_DIR_PATH = '/tmp'
tempfile.tempdir = TEMP_DIR_PATH

# Postgres settings
POSTGRES_HOST = '{}:{}'.format(os.getenv('POSTGRES_SERVICE_HOST', 'postgres'), os.getenv('POSTGRES_SERVICE_PORT', 5432))
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'ori')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME', 'ori_postgres_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'ori_postgres_password')

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from ocd_frontend.local_settings import *
except ImportError:
    pass
