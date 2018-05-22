#!/usr/bin/env bash

set -euo pipefail

main() {
    export FULL_VERSION=v${APP_VERSION}.${SEMAPHORE_BUILD_NUMBER}

    kubectl set image deployment/backend \
        backend=openstatefoundation/open-raadsinformatie-backend:${FULL_VERSION}
    kubectl set image deployment/frontend \
        frontend=openstatefoundation/open-raadsinformatie-frontend:${FULL_VERSION}

    kubectl get pods
}

main "$@"
