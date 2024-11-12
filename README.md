# Open Raadsinformatie API
Master: [![Build Status](https://semaphoreci.com/api/v1/jurrian/open-raadsinformatie/branches/master/shields_badge.svg)](https://semaphoreci.com/jurrian/open-raadsinformatie)
Develop: [![Build Status](https://semaphoreci.com/api/v1/jurrian/open-raadsinformatie/branches/develop/shields_badge.svg)](https://semaphoreci.com/jurrian/open-raadsinformatie)

Open Raadsinformatie (ORI) aims to collect and standardize governmental decision making documents of Dutch municipalities (gemeenten, provincies, waterschappen).
Open Raadsinformatie is a collaborative effort of the [Open State Foundation](https://openstate.eu/), [Ontola](https://ontola.io) and [VNG Realisatie](https://vngrealisatie.nl/).

## Important links

 - [Docs for API](/API-docs.md)
 - [Search engine](http://openbesluitvorming.nl/)
 - [Open Raadsinformatie homepage](http://www.openraadsinformatie.nl/)
 - [Official source code repository](https://github.com/openstate/open-raadsinformatie/)
 - [Issue tracker](https://github.com/openstate/open-raadsinformatie/issues)
 
## Installation and usage

See this guide to [install the Open Raadsinformatie API](https://github.com/openstate/open-raadsinformatie/blob/master/docs/installation.rst) using Docker, Vagrant or manually. There are also a few usage commands to get you started. Check out the [maintenance guide](maintenance_guide.md) for info on how to manage this project in production.

The docker-compose.yml specifies an external `docker_nginx-load-balancer` network. For local development use `docker network create docker_nginx-load-balancer` to create it.

Latest docker version uses "-" as separator when creating container names instead of "_". You can still get the old functionality by adding "--compatibility" to docker compose. So when using the latest Docker in development, use the following to start the containers:
`docker compose --compatibility -f docker-compose.yml -f docker-compose.dev.yml up --build -d`

## Testing
The next lines were copied from the Github workflow (which never ran) and still have to be tested:
- `docker compose --compatibility -f docker-compose.yml -f docker-compose.test.yml up --build -d`
- `docker exec ori_backend_1 bin/run_tests.sh 2>&1`
- `docker exec ori_backend_1 pylint ocd_backend -E -sy`

## Supported Sources

Data extraction support is available for the following source systems:

- [GO GemeenteOplossingen](https://www.gemeenteoplossingen.nl/)
- [Visma Roxit / GreenValley](https://www.greenvalley.nl/)
- [Notubiz](https://notubiz.nl/)
- [iBabs](https://www.ibabs.eu/nl/)
- [Parlaeus](https://parlaeus.nl/)
- [Tweede Kamer](https://opendata.tweedekamer.nl/documentatie/api-documentatie-20/)

## How to add your municipality

Get in touch with [Sander Bakker](sander.bakker@vng.nl) from VNG Realisatie.
Your griffie (municipality clerk) needs to formally agree that the data becomes open data, and the source system might need some configuration.

## Related repositories

- [openbesluitvorming](https://github.com/ontola/openbesluitvorming), the new search interface.

## Contributing

Please read through our [contributing guidelines](https://github.com/openstate/open-raadsinformatie/blob/master/CONTRIBUTING.rst).
Included are directions for opening issues, coding standards, and notes on development.

## Bugs and feature requests

Have a bug or a feature request? Please first read through and search for existing and closed issues. If your problem
or idea is not addressed yet, [please open a new issue](https://github.com/openstate/open-raadsinformatie/issues/new).

## Authors and contributors

The Open Raadsinformatie API was originally based on the
[Open Cultuur Data API](https://github.com/openstate/open-cultuur-data/).

Authors and contributors of both projects are:

* Bart de Goede ([@bartdegoede](https://twitter.com/bartdegoede))
* Justin van Wees ([@justin_v_w](https://twitter.com/justin_v_w))
* Breyten Ernsting ([@breyten](https://twitter.com/breyten))
* Sicco van Sas ([@siccovansas](https://twitter.com/siccovansas))
* Jurrian Tromp ([@jurrian](https://github.com/jurrian), [@ontola](https://github.com/ontola))
* Jorrit van Belzen ([@jorritb](https://github.com/jorritb), [@ontola](https://github.com/ontola))
* Joep Meindertsma ([@joepio](https://github.com/jorritb))
* Rob van Dijk ([@robvandijk](https://github.com/robvandijk))

Contributors:

* [DutchCoders](http://dutchcoders.io/)
* [Benno Kruit](https://github.com/bennokr)

## Copyright and license

The Open Raadsinformatie project is distributed under the [MIT license](https://opensource.org/licenses/MIT).
