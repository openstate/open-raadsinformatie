import logging.config
import os
import pickle
import tempfile

from bugsnag.handlers import BugsnagHandler
from kombu import Exchange, Queue
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

REDIS_HOST = os.getenv('REDIS_SERVICE_HOST', "redis")
REDIS_PORT = os.getenv('REDIS_SERVICE_PORT', 6379)
REDIS_URL = 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(ROOT_PATH)
LOCAL_DUMPS_DIR = os.path.join(PROJECT_PATH, 'local_dumps')
DUMPS_DIR = os.path.join(PROJECT_PATH, 'dumps')

# Use this timezone as default for timezone unaware dates
TIMEZONE = 'Europe/Amsterdam'

transformers_exchange = Exchange('transformers', type='direct')
enrichers_exchange = Exchange('enrichers', type='direct')
loaders_exchange = Exchange('loaders', type='direct')

CELERY_CONFIG = {
    'BROKER_URL': REDIS_URL,
    'CELERY_ACCEPT_CONTENT': ['ocd_serializer'],
    'CELERY_TASK_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_SERIALIZER': 'ocd_serializer',
    'CELERY_RESULT_BACKEND': 'ocd_backend.result_backends:OCDRedisBackend+%s' % REDIS_URL,
    'CELERY_MESSAGE_COMPRESSION': 'gzip',
    'CELERYD_HIJACK_ROOT_LOGGER': False,
    # ACKS_LATE prevents two tasks triggered at the same time to hang
    # https://wiredcraft.com/blog/3-gotchas-for-celery/
    'CELERY_TASK_ACKS_LATE': True,
    'CELERYD_PREFETCH_MULTIPLIER': 1,
    # Expire results after 30 minutes; otherwise Redis will keep
    # claiming memory for a day
    'CELERY_TASK_RESULT_EXPIRES': 1800,
    'CELERYD_REDIRECT_STDOUTS_LEVEL': 'INFO',
    'CELERY_ROUTES': {
        'ocd_backend.transformers.*': {
            'queue': 'transformers',
            'routing_key': 'transformers',
            'priority': 9,
        },
        'ocd_backend.enrichers.*': {
            'queue': 'enrichers',
            'routing_key': 'enrichers',
            'priority': 6,
        },
        'ocd_backend.loaders.*': {
            'queue': 'loaders',
            'routing_key': 'loaders',
            'priority': 3,
        },
        'ocd_backend.tasks.*': {
            'queue': 'loaders',
            'routing_key': 'loaders',
            'priority': 0,
        },
        'ocd_backend.pipeline.*': {
            'queue': 'loaders',
            'routing_key': 'loaders',
            'priority': 0,
        },
    },
    'CELERY_QUEUES': (
        Queue('transformers', transformers_exchange, routing_key='transformers'),
        Queue('enrichers', enrichers_exchange, routing_key='enrichers'),
        Queue('loaders', loaders_exchange, routing_key='loaders'),
    ),
    'CELERY_TASK_DEFAULT_QUEUE': 'transformers',
    'CELERY_TASK_DEFAULT_EXCHANGE': 'transformers',
    'CELERY_TASK_DEFAULT_ROUTING_KEY': 'transformers',
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


default_handlers = ['default', 'bugsnag']

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
            'handlers': default_handlers,
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': default_handlers,
            'level': 'INFO',
            'propagate': False,
        },
        'celery.worker': {
            'handlers': default_handlers,
            'level': 'DEBUG',
            'propagate': False,
            'filters': ['set_debug']
        },
        'celery.worker.strategy': {
            'handlers': default_handlers,
            'level': 'INFO',
            'propagate': False,
            'filters': ['set_debug']
        },
        'celery.worker.control': {
            'handlers': default_handlers,
            'level': 'DEBUG',
            'propagate': False,
            'filters': ['set_debug']
        },
        'celery.app.trace': {
            'handlers': default_handlers,
            'level': 'INFO',
            'propagate': False,
            # 'filters': ['set_debug']
        },
        'httpstream': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        },
        'elasticsearch': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        },
        'iso8601': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        },
        'kombu': {
            'handlers': default_handlers,
            'level': 'WARNING',
            'propagate': False,
        }
    },
    'root': {
        'handlers': default_handlers,
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
        asynchronous=False,
    )

    connect_failure_handler()

# Configure python logging system with LOGGING dict
logging.config.dictConfig(LOGGING)

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_SERVICE_HOST', 'elastic')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_SERVICE_PORT', 9200)

# The path of the directory used to store static files
DATA_DIR_PATH = os.path.join(PROJECT_PATH, 'data')

# The path of the directory used to store temporary files
TEMP_DIR_PATH = '/tmp'
tempfile.tempdir = TEMP_DIR_PATH

# The path of the JSON file containing the sources config
SOURCES_CONFIG_FILE = os.path.join(ROOT_PATH, 'sources/*')

ORI_CLASSIFIER_URL = 'http://{}:{}/classificeer'.format(os.getenv('CLASSIFIER_SERVICE_HOST', 'classifier'), os.getenv('CLASSIFIER_SERVICE_PORT', 5000))

# The default prefix used for all data
DEFAULT_INDEX_PREFIX = 'ori'

RESOLVER_BASE_URL = os.getenv('RESOLVER_BASE_URL', 'https://api.openraadsinformatie.nl/v%s/static' % MAJOR_VERSION)

# The User-Agent that is used when retrieving data from external sources
USER_AGENT = 'Open Raadsinformatie/%s.%s (+http://www.openraadsinformatie.nl/)' % (MAJOR_VERSION, MINOR_VERSION)

# The endpoint for the iBabs API
IBABS_WSDL = u'https://wcf.ibabs.eu/api/Public.svc?singleWsdl'

# The endpoint for the CompanyWebcast API
CWC_WSDL = u'https://services.companywebcast.com/meta/1.2/metaservice.svc?singleWsdl'

# define the location of pdftotext
PDF_TO_TEXT = u'pdftotext'
PDF_MAX_MEDIABOX_PIXELS = 5000000

# Exceptions that when raised should be autoretried by celery
AUTORETRY_EXCEPTIONS = []

# Kafka settings for DeltaLoader
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')
KAFKA_USERNAME = os.getenv('KAFKA_USERNAME')
KAFKA_PASSWORD = os.getenv('KAFKA_PASSWORD')
KAFKA_SESSION_TIMEOUT = os.getenv('KAFKA_SESSION_TIMEOUT', 5000)
KAFKA_MESSAGE_KEY = os.getenv('KAFKA_MESSAGE_KEY', 'ori_delta_message')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'ori-delta')

# Postgres settings
POSTGRES_HOST = '{}:{}'.format(os.getenv('POSTGRES_SERVICE_HOST', 'postgres'), os.getenv('POSTGRES_SERVICE_PORT', 5432))
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'ori')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME', 'ori_postgres_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'ori_postgres_password')

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from local_settings import *
except ImportError:
    pass
