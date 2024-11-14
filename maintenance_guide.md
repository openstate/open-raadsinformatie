# Maintenance guide ORI

## Deploy
- There is currently no automatic deploy
- When deploying, on server:
  - git pull
  - sudo docker compose --compatibility up --build -d
  - Then restart containers if necessary
    - sudo docker compose restart backend loader

## Adding municipalities

- New municipalities are probably added to the issue tracker.
- Identify supplier (Notubiz / go / etc)
- Open the relevant `ocd_backend/sources` file.
- Duplicate bottom municipality
- Set key (equal to shortname, dashes allowed)
- Allamak code: https://allmanak.nl/cat/1/Gemeenten (https://allmanak.nl/cat/32/Waterschappen), search name, get ID from URL
- For CBS code: https://www.cbs.nl/nl-nl/onze-diensten/methoden/classificaties/overig/gemeentelijke-indelingen-per-jaar/indeling-per-jaar/gemeentelijke-indeling-op-1-januari-2024
- Optionally set `source_name` if municipality name can't be properly derived from shortname.
- Optionally set `municipality_prefix` if municipality has multiple suppliers per region.
- The next step depends on supplier, see below
- Push to master
- `ssh` to `wolf` (ask Breyten)
- sh to `redis` (see [redis](#redis))
- `select 1` for setting individual municipalities
- `set "ori.{supplier}.{key}" "all daily monthly"` add municipality
- `set _all.start_date` set start date for a new run (e.g. when some specific run has to be done)
- `exit`
- see [#starting-a-run](#starting-a-run) below to sh into `backend-${id}`
- start the extraction process for the new municipality `sudo docker exec ori_backend_1 ./manage.py extract process all --source_path=ori.notubiz.weesp`. 
They will be set in a list for `celery`, which means that they will be processed in time.
- You can track the progress in the logs under /var/lib/docker/containers for ori_backend_1 and ori_loader_1.
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

- Go to redis (see devops), set source value to `archived` for the older one.

## Finding bugs

- Bugs are reported to [Bugsnag](https://app.bugsnag.com/argu/ori/errors).


## Troubleshooting

- Not enough available disk space can cause downtime. Elastic starts to have issues at 80% disk usage - it starts moving stuff to other instances. Fix this by making the disk larger and copying the contents.
- When dealing with IBabs issues, use SoapUI.
- When finding logs for a municipality, use the GCP querybuilder with `textPayload:municipality`


## Folder structure

- **ocd_backend** contains most logic
  - **bin**
  - **models** Use OpenGov definitions
  - **sources** contain municipalities config
  - **extractor** Responsible for fetching data
  - **loader** Responsible for writing data (e.g. elastic and linked-delta's)
  - **transformers** Responsible for mapping data
  - **enrichers** Extracting text from PDFs, adding locations, adding themes

## HTTPS (SSL / TLS certificates)

This project uses [`cert-manager`](https://cert-manager.io/docs/) for creating certificates.

## Deleting resources from Elastic

- `sudo docker exec -it ori_elastic_1 sh` get a shell in a running elastic container
- Send an HTTP DELETE to the ID: `curl -X DELETE 0.0.0.0:9200/${index}/${type}/${id}`, e.g. `curl -X DELETE 0.0.0.0:9200/ori_vlaardingen_20190809125128/_doc/1234567`

## Script to list all sources (for excel sheets)

Sometimes VNG wants a list of municipalities. You can use `./fetch_municipalities.sh` to fetch the data for all suppliers and output it in a format suitable for Excel sheets.
