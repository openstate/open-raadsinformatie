import logging.config
import os
import subprocess
import pickle
import tempfile

from requests import exceptions
from urllib3.exceptions import MaxRetryError, ReadTimeoutError
from requests import ConnectTimeout
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

RELEASE_STAGE = os.getenv('RELEASE_STAGE')

# host.docker.internal:8090; start proxy with ssh -gD 8090 wolf
PROXY_HOST = os.getenv('PROXY_HOST') if RELEASE_STAGE == 'development' else None
PROXY_PORT = os.getenv('PROXY_PORT') if RELEASE_STAGE == 'development' else None

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
    'broker_url': REDIS_URL,
    'accept_content': ['ocd_serializer'],
    'task_serializer': 'ocd_serializer',
    'result_serializer': 'ocd_serializer',
    'result_backend': 'ocd_backend.result_backends:OCDRedisBackend+%s' % REDIS_URL,
    'result_compression': 'gzip',
    'worker_hijack_root_logger': False,
    # ACKS_LATE prevents two tasks triggered at the same time to hang
    # https://wiredcraft.com/blog/3-gotchas-for-celery/
    'CELERY_TASK_ACKS_LATE': True,
    'worker_prefetch_multiplier': 1,
    # Expire results after 30 minutes; otherwise Redis will keep
    # claiming memory for a day
    'result_expires': 1800,
    'worker_redirect_stdouts_level': 'INFO',
    'task_routes': {
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
    'task_queues': (
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


default_handlers = ['default']

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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'advanced'
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

ORI_CLASSIFIER_HOST = os.getenv('CLASSIFIER_SERVICE_HOST', 'classifier')
ORI_CLASSIFIER_PORT = os.getenv('CLASSIFIER_SERVICE_PORT', 5000)

LOCLINKVIS_HOST = os.getenv('LOCLINKVIS_SERVICE_HOST', 'loclinkvis')
LOCLINKVIS_PORT = os.getenv('LOCLINKVIS_SERVICE_PORT', 8080)

# The default prefix used for all data
DEFAULT_INDEX_PREFIX = 'ori'

RESOLVER_BASE_URL = os.getenv('RESOLVER_BASE_URL', 'https://api.openraadsinformatie.nl/v%s/resolve' % MAJOR_VERSION)

# The User-Agent that is used when retrieving data from external sources
USER_AGENT = 'Open Raadsinformatie/%s.%s (+http://www.openraadsinformatie.nl/)' % (MAJOR_VERSION, MINOR_VERSION)

# The endpoint for the iBabs API
IBABS_WSDL = 'https://wcf.ibabs.eu/api/Public.svc?singleWsdl'

# The endpoint for the CompanyWebcast API
CWC_WSDL = 'https://services.companywebcast.com/meta/1.2/metaservice.svc?singleWsdl'

# Exceptions that when raised should be autoretried by celery
AUTORETRY_EXCEPTIONS = [MaxRetryError, exceptions.RetryError, ReadTimeoutError, ConnectTimeout, ConnectionError, exceptions.ConnectionError]
AUTORETRY_RETRY_BACKOFF = 30
RETRY_MAX_RETRIES = 6 # 9 RVD temporarily set lower to speed up overall reindexing
AUTORETRY_RETRY_BACKOFF_MAX = 15360

# Postgres settings
POSTGRES_HOST = '{}:{}'.format(os.getenv('POSTGRES_SERVICE_HOST', 'postgres'), os.getenv('POSTGRES_SERVICE_PORT', 5432))
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'ori')
POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME', 'ori_postgres_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'ori_postgres_password')

# Sentry DSN
SENTRY_DSN = os.getenv('SENTRY_DSN')
if RELEASE_STAGE == 'development':
    SENTRY_ENVIRONMENT = 'development' 
elif RELEASE_STAGE == 'testing':    
    SENTRY_ENVIRONMENT = 'testing'
else:
    SENTRY_ENVIRONMENT = 'production2' # RVD CHANGE BACK TO PRODUCTION WHEN NEW SERVER BECOMES MAIN SERVER

def get_ocr_version():
    tesseract_version = subprocess.check_output("apk info tesseract-ocr | head -n 1 | awk '{print $1}'", shell=True).decode().strip()
    # See also requirements.txt
    return f"tesserocr==2.7.1,{tesseract_version}"
OCR_VERSION = get_ocr_version()

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from ocd_backend.local_settings import *
except ImportError:
    pass
