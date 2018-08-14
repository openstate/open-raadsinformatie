import logging.config
import os
import pickle

from bugsnag.handlers import BugsnagHandler
from kombu.serialization import register
from pythonjsonlogger import jsonlogger
from version import __version__, __version_info__

register('ocd_serializer', pickle.dumps, pickle.loads,
         content_encoding='binary',
         content_type='application/x-pickle2')

APP_VERSION = __version__
MAJOR_VERSION = __version_info__[0]
MINOR_VERSION = __version_info__[1]

BUGSNAG_APIKEY = os.getenv('BUGSNAG_APIKEY')

RELEASE_STAGE = os.getenv('RELEASE_STAGE', 'development')

REDIS_HOST = os.getenv('REDIS_SERVER_HOST', "redis")
REDIS_PORT = os.getenv('REDIS_SERVER_PORT', "6379")
REDIS_URL = 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(ROOT_PATH)
LOCAL_DUMPS_DIR = os.path.join(PROJECT_PATH, 'local_dumps')
DUMPS_DIR = os.path.join(PROJECT_PATH, 'dumps')

# Use this timezone as default for timezone unaware dates
TIMEZONE = 'Europe/Amsterdam'

CELERY_CONFIG = {
    'BROKER_URL': REDIS_URL,
    'CELERY_ACCEPT_CONTENT': ['ocd_serializer'],
    'CELERY_TASK_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_BACKEND': 'ocd_backend.result_backends:OCDRedisBackend+%s' % REDIS_URL,
    'CELERY_IGNORE_RESULT': False,
    'CELERY_MESSAGE_COMPRESSION': 'gzip',
    'CELERYD_HIJACK_ROOT_LOGGER': False,
    'CELERY_DISABLE_RATE_LIMITS': True,
    # ACKS_LATE prevents two tasks triggered at the same time to hang
    # https://wiredcraft.com/blog/3-gotchas-for-celery/
    'CELERY_ACKS_LATE': True,
    'WORKER_PREFETCH_MULTIPLIER': 1,
    # Expire results after 30 minutes; otherwise Redis will keep
    # claiming memory for a day
    'CELERY_TASK_RESULT_EXPIRES': 1800,
    'CELERY_REDIRECT_STDOUTS_LEVEL': 'INFO'
}


class SetDebugFilter(logging.Filter):
    """ This filter decreases the logrecord to DEBUG """

    def filter(self, record):
        # Only filter when smaller then warning
        if record.levelno < 30:
            # Downgrade level to debug
            record.levelno = 10
            record.levelname = 'DEBUG'
        return True


class StackdriverJsonFormatter(jsonlogger.JsonFormatter, object):
    """ Formats the record to a Google Stackdriver compatible json string """

    def __init__(self, fmt="%(levelname) %(message)", *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record['severity'] = log_record['levelname']
        del log_record['levelname']
        return super(StackdriverJsonFormatter, self).process_log_record(log_record)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Existing loggers are 'disabled' below
    'filters': {
        'set_debug': {
            '()': SetDebugFilter,
        }
    },
    'formatters': {
        'basic': {
            'format': '[%(module)s] %(levelname)s %(message)s'
        },
        'advanced': {
            'format': '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'stackdriver': {
            '()': StackdriverJsonFormatter,
        }
    },
    'handlers': {
        'default': {
            # Basic logging when not running in docker or stackdriver
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'advanced',
            'filename': os.path.join(PROJECT_PATH, 'log', 'backend.log')
        },
        'bugsnag': {
            'level': 'WARNING',
            '()': BugsnagHandler,
        }
    },
    'loggers': {
        'ocd_backend': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.worker.strategy': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
            'filters': ['set_debug']
        },
        'celery.app.trace': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
            'filters': ['set_debug']
        },
        'neo4j.bolt': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'httpstream': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'elasticsearch': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'iso8601': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'kombu': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['default', 'bugsnag'],
        'level': 'WARNING',
        'propagate': False
    },
}

if os.path.exists(os.path.join(PROJECT_PATH, 'log', 'stdout')):
    # Set default handler to write to docker logs via /proc/1/fd/1 symlink
    # (see Dockerfile)
    LOGGING['handlers']['default'] = {
        'level': 'DEBUG',
        'class': 'logging.FileHandler',
        'formatter': 'basic',
        'filename': os.path.join(PROJECT_PATH, 'log', 'stdout')
    }

if os.getenv('GCE_STACKDRIVER'):
    # Set default handler to format for Google Stackdriver logging
    LOGGING['handlers']['default'] = {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'stackdriver',
        'stream': 'ext://sys.stdout',
    }

if BUGSNAG_APIKEY:
    import bugsnag
    from .utils.bugsnag_celery import connect_failure_handler

    bugsnag.configure(
        api_key=BUGSNAG_APIKEY,
        project_root=ROOT_PATH,
        release_stage=RELEASE_STAGE,
        app_version=APP_VERSION,
    )

    connect_failure_handler()

# Configure python logging system with LOGGING dict
logging.config.dictConfig(LOGGING)

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'elastic-endpoint')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_PORT', 9200)

NEO4J_URL = os.getenv('NEO4J_URL', 'bolt://neo4j:7687')
try:
    NEO4J_USER, NEO4J_PASSWORD = os.getenv('NEO4J_AUTH', 'neo4j/development').split('/')
except (ValueError, AttributeError):
    NEO4J_USER, NEO4J_PASSWORD = None, None

# The path of the directory used to store temporary files
TEMP_DIR_PATH = os.path.join(ROOT_PATH, 'temp')

# The path of the directory used to store static files
DATA_DIR_PATH = os.path.join(PROJECT_PATH, 'data')

# The path of the JSON file containing the sources config
SOURCES_CONFIG_FILE = os.path.join(ROOT_PATH, 'sources/*')

# The name of the index containing documents from all sources
COMBINED_INDEX = 'ori_combined_index'

# The default prefix used for all data
DEFAULT_INDEX_PREFIX = 'ori'

RESOLVER_BASE_URL = os.getenv('RESOLVER_BASE_URL', 'http://api.openraadsinformatie.nl/v%s/resolve' % MAJOR_VERSION)
RESOLVER_URL_INDEX = 'ori_resolver'

# The User-Agent that is used when retrieving data from external sources
USER_AGENT = 'Open Raadsinformatie/%s.%s (+http://www.openraadsinformatie.nl/)' % (MAJOR_VERSION, MINOR_VERSION)

# URL where of the API instance that should be used for management commands
# Should include API version and a trailing slash.
# Can be overridden in the CLI when required, for instance when the user wants
# to download dumps from another API instance than the one hosted by OpenState
API_URL = os.getenv('API_URL', 'http://frontend:5000/v%s/' % MAJOR_VERSION)

# The endpoint for the iBabs API
IBABS_WSDL = u'https://www.mijnbabs.nl/iBabsWCFService/Public.svc?singleWsdl'

# The endpoint for the CompanyWebcast API
CWC_WSDL = u'https://services.companywebcast.com/meta/1.2/metaservice.svc?singleWsdl'

# define the location of pdftotext
PDF_TO_TEXT = u'pdftotext'
PDF_MAX_MEDIABOX_PIXELS = 5000000

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from local_settings import *
except ImportError:
    pass
