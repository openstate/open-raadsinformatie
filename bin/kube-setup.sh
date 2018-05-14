#!/usr/bin/env bash

set -euo pipefail

main() {
	# Pre-req for gcloud install
	sudo apt-get update
	sudo apt-get install -y apt-transport-https

	# Copied from the official install instructions on https://cloud.google.com/sdk/downloads#apt-get
	export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
	echo "deb https://packages.cloud.google.com/apt ${CLOUD_SDK_REPO} main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
	sudo apt-get update
	sudo apt-get install -y google-cloud-sdk kubectl

	# Copied from the docker-compose docs:
	#sudo curl -L "https://github.com/docker/compose/releases/download/1.9.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	#sudo chmod +x /usr/local/bin/docker-compose

	gcloud --version
	kubectl version -c
	docker-compose --version

	echo "Authenticating gcloud service account"
	gcloud auth activate-service-account \
		--key-file "${GOOGLE_APPLICATION_CREDENTIALS}" \
		--project "${GOOGLE_PROJECT_ID}"

	echo "Authenticating to GCR"
	gcloud docker --authorize-only --project "${GOOGLE_PROJECT_ID}"

	echo "Configuring kubectl"
	gcloud container clusters get-credentials "${GOOGLE_PROJECT_CLUSTER}" \
		--project "${GOOGLE_PROJECT_ID}" \
		--zone "${GOOGLE_PROJECT_ZONE}"
}

main "$@"
