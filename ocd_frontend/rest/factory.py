from flask import Flask

# noinspection PyUnresolvedReferences
####### import log  # needed for init logging
import settings
from es import ElasticsearchService
from helpers import register_blueprints
from settings import BUGSNAG_APIKEY


def create_app_factory(package_name, package_path, settings_override=None):
    """Returns a :class:`Flask` application instance configured with
    project-wide functionality.

    :param package_name: application package name.
    :param package_path: application package path.
    :param settings_override: a dictionary of settings to override.
    """
    app = Flask(package_name, instance_relative_config=True)

    app.config.from_object(settings)
    app.config.from_object(settings_override)

    app.es = ElasticsearchService(app.config['ELASTICSEARCH_HOST'],
                                  app.config['ELASTICSEARCH_PORT'])

    register_blueprints(app, package_name, package_path)

    return app
