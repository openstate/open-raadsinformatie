# Google Cloud Endpoints
Using Google Cloud Endpoints makes it easy to develop, deploy, protect and monitor APIs.
It provides access to the frontend service through the endpoints-service which can be found here:
`deployment/ori/templates/endpoints-deployment.yaml`.

The `host` value in swagger should correspond to the `endpointsHost` in Helm/Kubernetes.
The `version` in swagger files should match the app version when updated to a new revision.

When logged-in in gcloud in the right project, use the following command to create or update an endpoint.
```bash
$ gcloud endpoints services deploy production.yaml
```

For more information see: https://cloud.google.com/endpoints/docs/openapi/get-started-compute-engine-docker
