#!/usr/bin/env bash

set -euo pipefail

main() {
	kubectl apply -f kubernetes/backend-deployment.yaml --namespace "${SEMAPHORE_SERVER_NAME}"
	kubectl apply -f kubernetes/frontend-deployment.yaml --namespace "${SEMAPHORE_SERVER_NAME}"

	kubectl get pods --namespace "${SEMAPHORE_SERVER_NAME}"
}

main "$@"
