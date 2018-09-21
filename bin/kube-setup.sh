#!/usr/bin/env bash

set -euo pipefail

main() {
	# Pre-req for gcloud install
	# install-package is a semaphoreci wrapper for apt-get
	install-package apt-transport-https

	# Copied from the official install instructions on https://cloud.google.com/sdk/downloads#apt-get
	export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
	echo "deb https://packages.cloud.google.com/apt ${CLOUD_SDK_REPO} main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

    # Temporary fix for https://github.com/travis-ci/travis-ci/issues/9361
    sudo apt-get install -y dpkg

	install-package --update-new google-cloud-sdk kubectl

	gcloud --version
	kubectl version -c
	docker-compose --version

	echo "Authenticating gcloud service account"
	gcloud auth activate-service-account \
		--key-file "${GOOGLE_APPLICATION_CREDENTIALS}" \
		--project "${GOOGLE_PROJECT_ID}"

	echo "Authenticating to GCR"
	gcloud auth configure-docker -q --project "${GOOGLE_PROJECT_ID}"

	echo "Configuring kubectl"
	gcloud container clusters get-credentials "${GOOGLE_PROJECT_CLUSTER}" \
		--project "${GOOGLE_PROJECT_ID}" \
		--zone "${GOOGLE_PROJECT_ZONE}"

	echo "Set namespace context"
	kubectl config set-context $(kubectl config current-context) \
	    --namespace="${SEMAPHORE_SERVER_NAME}"
}

main "$@"
