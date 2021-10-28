# Maintenance guide ORI

## Setting up

- Spin up a Kubernetes cluster (we used google cloud for this)
- Set up the necessary persistence layers
- Install `kubectl` and `gcloud` on your local device
- Sign in using `gcloud`
- `kubectl apply` all the `deployment/production/*` files
- Make sure all the domain names in the `ingress.yaml` are set up correctly
- Run migrations to setup database (I assume `alembic` is used for this)
- Set up the secrets (see below)

## Secrets

I encountered these in kubernetes:

```sh
# Still used:
KAFKA_PASSWORD
KAFKA_USERNAME
POSTGRES_PASSWORD
POSTGRES_USERNAME

# Probably outdated:
SEARCH_GLOSS_CLIENT_ID
SEARCH_GLOSS_CLIENT_SECRET
NEO4J_AUTH
harderwijk.cwc_password
harderwijk.cwc_username
overbetuwe.cwc_password
overbetuwe.cwc_username
utrecht.cwc_password
utrecht.cwc_username
```

You can get secrets using `kubectl get secret secrets -n production -o jsonpath='{.data.POSTGRES_USERNAME}' | base64 --decode`

## Adding municipalities

- New municipalities are probably added to the issue tracker.
- Identify supplier (Notubiz / go / etc)
- Open the relevant `ocd_backend/sources` file.
- Duplicate bottom municipality
- Set key (equal to shortname, dashes allowed)
- Allamak code: https://allmanak.nl/cat/1/Gemeenten, search name, get ID from URL
- For CBS code: https://www.cbs.nl/nl-nl/onze-diensten/methoden/classificaties/overig/gemeentelijke-indelingen-per-jaar/indeling%20per%20jaar/gemeentelijke-indeling-op-1-januari-2020
- Optionally set `source_name` if municipality name can't be properly derived from shortname.
- Optionally set `municipality_prefix` if municipality has multiple suppliers per region.
- The next step depends on supplier, see below
- Push and a Docker image is built (tests are run) and pushed to github container registry, which you can see at: `https://github.com/openstate/open-raadsinformatie/pkgs/container/open-raadsinformatie/versions`
- sh to `redis` (see [redis](#redis))
- `select 1` for setting individual municipalities
- `set "ori.{supplier}.{key}"  "all daily monthly"` add municipality
- `exit`
- Make sure the image version running in GCLoud is the [latest one](https://github.com/openstate/open-raadsinformatie/pkgs/container/open-raadsinformatie/versions) containing the new municipalities. You can check the [backend deployment](https://console.cloud.google.com/kubernetes/deployment/europe-west4-a/ori-cluster/production/backend/yaml/edit?authuser=1&project=open-raadsinformatie-52162). The last number of the version should be the build number of . If this is not a match, you can manually set it in the deployment YAML file.
- see [#starting-a-run](#starting-a-run) below to sh into `backend-${id}`
- start the extraction process for the new municipality `/opt/ori $ python manage.py extract process all --source_path=ori.notubiz.weesp`. They will be set in a list for `celery`, which means that they will be processed in time. You can scale up the amount of workers for `backend` in Google, but it's probably not necessary.
- You can track the progress in the Google cloud logs.
- Update the status per municipality (importing, finished) in the github issue tracker.

### Supplier specific: Notubiz

- Go to https://api.notubiz.nl/organisations

### Supplier specific: Ibabs

- For finding `ibabs_sitename`, google for `ibabs ${municipality_name}` and derive it from the URL
- Duplicate
- Exclcude / include are rarely required, but can be useful if one instance is shared across municipalitites

### Supplier specific: GemeenteOplossingen

- Usually trying a `base_url` that makes sense works fine

## Municipality Changing supplier

- Go to redis (see devops), set source value to "archived" for the older one.

## Finding bugs

- Bugs are reported to [Bugsnag](https://app.bugsnag.com/argu/ori/errors).

## redis

- The environment is [running on google cloud](https://console.cloud.google.com/kubernetes/list?project=open-raadsinformatie-52162&authuser=1&folder&organizationId). Make sure you've installed the `gcloud` cli tool, and use `gcloud auth login` to get access to the `open-raadsinformatie` account.
- connect to cluster with `gcloud` cli. Visit gcloud cluster, press `actions` and search for a `connect` command similar to `gcloud container clusters get-credentials ori-cluster --zone europe-west4-a --project open-raadsinformatie-52162`
- `kubectl get -A pods | grep redis` to get the name for the redis pod.
- `kubectl exec -it -n production ${name-of-redis-pod} redis-cli` to open the redis CLI.
- `select 0` for generic settings and pipelines
  - `keys _*` see all intervals¸ e.g. the base start date
  - `set _all.start_date` set start date for a new run (e.g. when some specific run has to be done)
- `select 1` for the sources (municipalities / provinces) settings
  - `get ori.ibabs.aalsmeer` => see current status
  - `set "ori.ibabs.{key}"  "all daily monthly"` add municipality

## Starting a run

- `kubectl get -A pods | grep backend`, pick a running one
- `kubectl exec -it -n production ${name-of-pod} sh`
- Import all municipalities (takes a couple of days): `python manage.py extract process all` (see manage.py for more options and commands)

## Troubleshooting

- Not enough available disk space can cause downtime. Elastic starts to have issues at 80% disk usage - it starts moving stuff to other instances. Fix this by making the disk larger and copying the contents.
- When dealing with IBabs issues, use SoapUI.
- When finding logs for a municipality, use the GCP querybuilder with `textPayload:municipality`

## Reverting a back-up

- Go to GCP -> Kubernetes -> Snapshots
- The snapshot schedule `postgres-weekly` is actually elastic
- Go to disks, create disk, standard disk, source type -> snapshot2

# Folder structure

- **Deployments** for kubernetes files
- **ocd_backend** contains most logic
  - **bin** e.g. kubernetes deploy script
  - **models** Use OpenGov definitions
  - **sources** contain municipalities config
  - **extractor** Responsible for fetching data
  - **loader** Responsible for writing data (e.g. elastic and linked-delta's)
  - **transformers** Responsible for mapping data
  - **enrichers** Extracting text from PDFs, adding locations, adding themes

### HTTPS (SSL / TLS certificates)

This project uses [`cert-manager`](https://cert-manager.io/docs/) for creating certificates.
