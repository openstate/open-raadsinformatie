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

Latest docker version uses "-" as separator when creating container names instead of "_". You can still get the old functionality by adding "--compatibility" to docker compose. So when using the latest Docker in development, use the following to start the containers:
`docker compose --compatibility -f docker-compose.yml -f docker-compose.dev.yml up --build -d`

The Nginx container was installed separately in production. To mimic this in development, clone `https://github.com/openstate/nginx-load-balancer/`, follow the instructions in `INSTALL.txt` and start the container with `docker compose --compatibility up -d`


## Testing
The next lines were copied from the Github workflow (which never actually ran):
- `docker compose --compatibility -f docker-compose.yml -f docker-compose.test.yml up --build -d`
- `docker exec ori_backend_1 bin/run_tests.sh 2>&1`
- `docker exec ori_backend_1 pylint ocd_backend -E -sy`


## Getting data in development
Sometimes it is necessary to manually get data from e.g. iBabs for troubleshooting. The problem is that iBabs only allows whitelisted
IP addresses to connect. In our case connections from wolf are allowed, so any query you want to execute should be proxied via wolf:
- In a terminal setup port forwarding: `ssh -gD 8090 wolf`
- To get data edit and run the `manual_retrieval.py` script from Docker container `ori_backend_1`. This script uses the proxy via
       
       session.proxies = {
            'http': 'socks5://host.docker.internal:8090',
            'https': 'socks5://host.docker.internal:8090'
        }
- You can test the proxy setup by running e.g. `curl --proxy socks5://host.docker.internal:8090 https://www.nu.nl` in the container        

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
