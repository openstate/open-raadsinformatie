#!/usr/bin/env bash

set -euo pipefail

main() {
    APP_VERSION=$(python -c "import version; print version.__version__")

    export FULL_VERSION=v${APP_VERSION}.${BRANCH_NAME}-${SEMAPHORE_BUILD_NUMBER}

    kubectl set image deployment/backend \
        backend=openstatefoundation/open-raadsinformatie-backend:${FULL_VERSION}
    kubectl set image deployment/frontend \
        frontend=openstatefoundation/open-raadsinformatie-frontend:${FULL_VERSION}

    kubectl get pods
}

main "$@"
