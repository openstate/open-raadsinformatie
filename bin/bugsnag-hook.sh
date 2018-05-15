#!/usr/bin/env bash

export APP_VERSION=1.0.0
curl https://build.bugsnag.com/ \
  --header "Content-Type: application/json" \
  --data "{
    'apiKey': '$BUGSNAG_APIKEY',
    'appVersion': '$APP_VERSION.$SEMAPHORE_BUILD_NUMBER',
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
