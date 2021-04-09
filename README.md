# Open Raadsinformatie API
Master: [![Build Status](https://semaphoreci.com/api/v1/jurrian/open-raadsinformatie/branches/master/shields_badge.svg)](https://semaphoreci.com/jurrian/open-raadsinformatie)
Develop: [![Build Status](https://semaphoreci.com/api/v1/jurrian/open-raadsinformatie/branches/develop/shields_badge.svg)](https://semaphoreci.com/jurrian/open-raadsinformatie)

Open Raadsinformatie (ORI) aims to collect and standardize governmental decision making data of Dutch municipalities.
This includes Meetings, Agenda Items, Documents, Motions and more.
Open Raadsinformatie is a collaborative effort of the [Open State Foundation](https://openstate.eu/), [Argu](https://argu.co) / [Ontola](https://ontola.io) and [VNG Realisatie](https://vngrealisatie.nl/).

## Important links

 - [Open Raadsinformatie homepage](http://www.openraadsinformatie.nl/)
 - [Official source code repository](https://github.com/openstate/open-raadsinformatie/)
 - [Issue tracker](https://github.com/openstate/open-raadsinformatie/issues)
 - [Search engine](http://zoek.openraadsinformatie.nl/)
 - [New search engine (beta)](https://ori.argu.co)
 - [Docs for V1 API](http://docs.openraadsinformatie.nl)

## Installation and usage

See this guide to [install the Open Raadsinformatie API](https://github.com/openstate/open-raadsinformatie/blob/master/docs/installation.rst) using Docker, Vagrant or manually. There are also a few usage commands to get you started. Check out the [maintenance guide](maintenance_guide.md) for info on how to manage this project in production.

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

- [ori-search](https://github.com/ontola/ori-search/), the new search interface.
- [ori_api](https://github.com/ontola/ori_api/), the `id.` REST api.

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

Contributors:

* [DutchCoders](http://dutchcoders.io/)
* [Benno Kruit](https://github.com/bennokr)

## Copyright and license

The Open Raadsinformatie project is distributed under the [MIT license](https://opensource.org/licenses/MIT).
