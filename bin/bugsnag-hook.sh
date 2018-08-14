#!/usr/bin/env bash

APP_VERSION=$(python -c "import version; print version.__version__")

curl https://build.bugsnag.com/ \
  --header "Content-Type: application/json" \
  --data "{
    'apiKey': '$BUGSNAG_APIKEY',
    'appVersion': '$APP_VERSION',
    'releaseStage': '$SEMAPHORE_SERVER_NAME',
    'builderName': '$DEPLOY_AUTHOR_NAME',
    'sourceControl': {
      'provider': 'github',
      'repository': 'https://github.com/openstate/open-raadsinformatie',
      'revision': '$REVISION'
    },
    'metadata': {
      'branch': '$BRANCH_NAME',
      'build': '$SEMAPHORE_BUILD_NUMBER',
      'deploy': '$SEMAPHORE_DEPLOY_NUMBER',
      'trigger': '$SEMAPHORE_TRIGGER_SOURCE'
    }
  }"
