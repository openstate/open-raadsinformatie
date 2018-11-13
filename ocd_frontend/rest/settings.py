import logging.config
import os.path

from bugsnag.handlers import BugsnagHandler
from pythonjsonlogger import jsonlogger

DEBUG = True

APP_VERSION = os.getenv('APP_VERSION', None)

BUGSNAG_APIKEY = os.getenv('BUGSNAG_APIKEY')

RELEASE_STAGE = os.getenv('RELEASE_STAGE', 'production')

# Elasticsearch
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'elastic-endpoint')
ELASTICSEARCH_PORT = os.getenv('ELASTICSEARCH_PORT', 9200)

# The default number of hits to return for a search request via the REST API
DEFAULT_SEARCH_SIZE = 10

# The max. number of hits to return for a search request via the REST API
MAX_SEARCH_SIZE = 100

# The default prefix used for all data
DEFAULT_INDEX_PREFIX = 'ori'

# The fields which can be used for sorting results via the REST API
SORTABLE_FIELDS = {
    'person': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'gender', 'name'],
    'organization': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'classification', 'name'],
    'meeting': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'classification', 'name', 'start_date',
        'location'],
    'agenda_item': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'classification', 'name', 'start_date',
        'location'],
    'motion': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'classification', 'name', 'date'],
    'vote_event': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score', 'classification', 'name', 'start_date'],
    'items': [
        'meta.source_id', 'meta.processing_started',
        'meta.processing_finished',
        'start_date', '_score']
}

# EXCLUDED_FIELDS_DEFAULT = ['all_text', 'source_data',
#                            'media_urls.original_url']
# EXCLUDED_FIELDS_SEARCH = ['all_text', 'media_urls.original_url']
#
# ALLOWED_INCLUDE_FIELDS_DEFAULT = ['all_text', 'source_data']
# ALLOWED_INCLUDE_FIELDS_SEARCH = ['all_text']

EXCLUDED_FIELDS_ALWAYS = ['enrichments', 'hidden']
EXCLUDED_FIELDS_DEFAULT = ['all_text', 'source_data',
                           'media_urls.original_url']
EXCLUDED_FIELDS_SEARCH = ['all_text', 'media_urls.original_url']

ALLOWED_INCLUDE_FIELDS_DEFAULT = []
ALLOWED_INCLUDE_FIELDS_SEARCH = []

SIMPLE_QUERY_FIELDS = {
    'person': [
        'biography^4', 'name^3', 'other_names^2',
        'memberships.organization.name^2',
        'memberships.role'],
    'organization': ['name^4', 'description'],
    'meeting': [
        'name^4', 'description^3', 'location', 'organization.name',
        'organization.description', 'sources.note^2', 'sources.description'],
    'agenda_item': [
        'name^4', 'description^3', 'location', 'organization.name',
        'organization.description', 'sources.note^2', 'sources.description'],
    'motion': [
        'name^4', 'text^3', 'organization.name', 'sources.note^2',
        'sources.description'],
    'vote_event': [
        'name^4', 'motion.text^3', 'organization.name', 'sources.note^2',
        'sources.description'],
    'items': [
        'name^4', 'description^3', 'location', 'organization.name',
        'organization.description', 'sources.note^2', 'sources.description',
        'biography^4', 'other_names^2', 'memberships.organization.name^2']
}

DOC_TYPE_DEFAULT = u'items'

# Definition of the ES facets (and filters) that are accessible through
# the REST API
COMMON_FACETS = {
    'processing_started': {
        'date_histogram': {
            'field': 'meta.processing_started',
            'interval': 'month'
        }
    },
    'processing_finished': {
        'date_histogram': {
            'field': 'meta.processing_finished',
            'interval': 'month'
        }
    },
    'source': {
        'terms': {
            'field': 'meta.source_id',
            'size': 10
        }
    },
    'collection': {
        'terms': {
            'field': 'meta.collection',
            'size': 10
        }
    },
    'rights': {
        'terms': {
            'field': 'meta.rights',
            'size': 10
        }
    },
    'index': {
        'terms': {
            'field': '_index',
            'size': 10
        }
    },
    'types': {
        'terms': {
            'field': '_type',
            'size': 10
        }
    },
    'start_date': {
        'date_histogram': {
            'field': 'start_date',
            'interval': 'month'
        }
    }
}

AVAILABLE_FACETS = {
    'organization': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        }
    },
    'person': {
        'gender': {
            'terms': {
                'field': 'gender',
                'size': 2
            }
        },
        'organization': {
            'terms': {
                'field': 'memberships.organization_id',
                'size': 10
            }
        }
    },
    'meeting': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        },
        'organization_id': {
            'terms': {
                'field': 'organization_id',
                'size': 10
            }
        },
        'location': {
            'terms': {
                'field': 'location',
                'size': 10
            }
        },
        'status': {
            'terms': {
                'field': 'status',
                'size': 10
            }
        },
        'start_date': {
            'date_histogram': {
                'field': 'start_date',
                'interval': 'month'
            }
        },
        'end_date': {
            'date_histogram': {
                'field': 'end_date',
                'interval': 'month'
            }
        }
    },
    'agenda_item': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        },
        'organization_id': {
            'terms': {
                'field': 'organization_id',
                'size': 10
            }
        },
        'location': {
            'terms': {
                'field': 'location',
                'size': 10
            }
        },
        'status': {
            'terms': {
                'field': 'status',
                'size': 10
            }
        },
        'start_date': {
            'date_histogram': {
                'field': 'start_date',
                'interval': 'month'
            }
        },
        'end_date': {
            'date_histogram': {
                'field': 'end_date',
                'interval': 'month'
            }
        }
    },
    'motion': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        },
        'organization_id': {
            'terms': {
                'field': 'organization_id',
                'size': 10
            }
        },
        'legislative_session_id': {
            'terms': {
                'field': 'legislative_session_id',
                'size': 10
            }
        },
        'creator_id': {
            'terms': {
                'field': 'creator_id',
                'size': 10
            }
        },
        'date': {
            'date_histogram': {
                'field': 'date',
                'interval': 'month'
            }
        },
        'requirement': {
            'terms': {
                'field': 'requirement',
                'size': 10
            }
        },
        'result': {
            'terms': {
                'field': 'result',
                'size': 10
            }
        }
    },
    'vote_event': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        },
        'organization_id': {
            'terms': {
                'field': 'organization_id',
                'size': 10
            }
        },
        'start_date': {
            'date_histogram': {
                'field': 'start_date',
                'interval': 'month'
            }
        },
        'end_date': {
            'date_histogram': {
                'field': 'end_date',
                'interval': 'month'
            }
        },
        'legislative_session_id': {
            'terms': {
                'field': 'legislative_session_id',
                'size': 10
            }
        }
    },
    'items': {
        'classification': {
            'terms': {
                'field': 'classification',
                'size': 10
            }
        }
    }
}


# For highlighting
COMMON_HIGHLIGHTS = {
    'source': {},
    'collection': {},
    'rights': {}
}

AVAILABLE_HIGHLIGHTS = {
    'organization': {
        'classification': {},
        'name': {},
        'description': {}
    },
    'person': {
        'name': {},
        'memberships.role': {},
        'area.name': {}
    },
    'meeting': {
        'classification': {},
        'location': {},
        'organization.name': {},
        'description': {},
        'sources.note': {},
        'sources.description': {}
    },
    'agenda_item': {
        'classification': {},
        'location': {},
        'organization.name': {},
        'description': {},
        'sources.note': {},
        'sources.description': {}
    },
    'motion': {
        'classification': {},
        'organization.name': {},
        'creator.name': {},
        'text': {},
        'sources.description': {}
    },
    'vote_event': {
        'classification': {},
        'organization.name': {},
        'creator.name': {},
        'text': {},
        'sources.description': {}
    },
    'items': {
        'classification': {},
        'name': {},
        'description': {}
    }
}

# The allowed date intervals for an ES data_histogram that can be
# requested via the REST API
ALLOWED_DATE_INTERVALS = ('day', 'week', 'month', 'quarter', 'year')

# Name of the Elasticsearch index used to store URL resolve documnts
RESOLVER_URL_INDEX = 'ori_resolver'

# Determines if API usage events should be logged
USAGE_LOGGING_ENABLED = True
# Name of the Elasticsearch index used to store logged events
USAGE_LOGGING_INDEX = 'ori_usage_logs'

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PATH = os.path.dirname(ROOT_PATH)
DATA_DIR_PATH = os.path.join(PROJECT_PATH, 'data')
STATIC_DIR_PATH = os.path.join(DATA_DIR_PATH, 'static')
LOCAL_DUMPS_DIR = os.path.join(PROJECT_PATH, 'local_dumps')
DUMPS_DIR = os.path.join(PROJECT_PATH, 'dumps')

# URL where of the API instance that should be used for management commands
# Should include API version and a trailing slash.
# Can be overridden in the CLI when required, for instance when the user wants
# to download dumps from another API instance than the one hosted by OpenState
API_URL = os.getenv('API_URL', 'http://frontend:5000/v1/')

# URL where collection dumps are hosted. This is used for generating full URLs
# to dumps in the /dumps endpoint
DUMP_URL = 'http://dumps.opencultuurdata.nl/'


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
    'disable_existing_loggers': False,
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
            'formatter': 'basic',
            'stream': 'ext://sys.stdout'
        },
        'bugsnag': {
            'level': 'WARNING',
            '()': BugsnagHandler,
        }
    },
    'loggers': {
        'ocd_frontend': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bugsnag': {
            'handlers': ['bugsnag']
        }
    },
    'root': {
        'handlers': ['default', 'bugsnag'],
        'level': 'INFO',
    },
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
    from bugsnag.handlers import BugsnagHandler

    # Needs to be called before dictConfig
    bugsnag.configure(
        api_key=BUGSNAG_APIKEY,
        project_root=ROOT_PATH,
        release_stage=RELEASE_STAGE,
        app_version=APP_VERSION,
    )

# Configure python logging system with LOGGING dict
logging.config.dictConfig(LOGGING)

THUMBNAILS_TEMP_DIR = '/tmp'

THUMBNAILS_MEDIA_TYPES = {'image/jpeg', 'image/png', 'image/tiff'}
THUMBNAILS_DIR = os.path.join(ROOT_PATH, '.thumbnail-cache')

THUMBNAIL_SMALL = 250
THUMBNAIL_MEDIUM = 500
THUMBNAIL_LARGE = 1000

THUMBNAIL_SIZES = {
    'large': {'size': (THUMBNAIL_LARGE, THUMBNAIL_LARGE), 'type': 'aspect'},
    'medium': {'size': (THUMBNAIL_MEDIUM, THUMBNAIL_MEDIUM), 'type': 'aspect'},
    'small': {'size': (THUMBNAIL_SMALL, THUMBNAIL_SMALL), 'type': 'aspect'},
    'large_sq': {'size': (THUMBNAIL_LARGE, THUMBNAIL_LARGE), 'type': 'crop'},
    'medium_sq': {'size': (THUMBNAIL_MEDIUM, THUMBNAIL_MEDIUM),
                  'type': 'crop'},
    'small_sq': {'size': (THUMBNAIL_SMALL, THUMBNAIL_SMALL), 'type': 'crop'},
}

THUMBNAIL_URL = '/media/'

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from local_settings import *
except ImportError:
    pass
