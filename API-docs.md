# OpenBesluitvorming / Open Raadsinformatie / Open Stateninformatie API docs

OpenBesluitvorming aims to make governmental decision making more transparent
by aggregating and standardizing meeting & decision data.
Currently, the API includes data from more than 300 municipalities and provinces.

As of March 2023, we only support the `Documents` class.
These represent imported PDF(-like) resources and their plaintext representations.
This is what >90% of our users want, and is >99% of the data that we have.
Other classes (like meetings, agenda items) are often still imported if they work, but we will not prioritize fixing these if there are import issues with them.

## Elastic Endpoint

Endpoint: `https://api.openraadsinformatie.nl/v1/elastic/`

This is an ElasticSearch endpoint, which offers powerful query and full-text search capabilities.

The repo and issue tracker for this API can be found [here](https://github.com/openstate/open-raadsinformatie).
Read the [Elastic v7.0](https://www.elastic.co/guide/en/elasticsearch/reference/7.0/index.html) docs for more information.
Only [specific Elastic endpoints](https://github.com/openstate/open-raadsinformatie/blob/master/deployment/endpoints/production.yaml) are publicly available.
This is to prevent (malicious or accidental) write / remove commands.

If you want to know the mapping for Elastic, visit `https://api.openraadsinformatie.nl/v1/elastic/ori_amers*/_mapping`. Replace `ori_amsers` with the index that you're interested in.

If you want to see some examples of how to query this endpoint, check out [`example_requests.http`](/example_requests.http).

## API Versioning & deprecation

APIs change over time, and some of these changes could break implementations.
At all times, we try to minimize these breaking changes.
When these are necessary, however, we will upgrade the API version.
If you want to receive notifications prior to breaking API changes, subscribe by mailing to [joep@argu.co](mailto:joep@argu.co?subject=ORI API versioning) with the subject: "ORI API versioning".

- The REST API should be considered stable.
- The Elastic API has various undocument endpoints.

### Changes from V0 to V1

- ElasticSearch was upgraded from 5 to 7 ([upgrade guide](https://www.elastic.co/guide/en/cloud/current/ec-upgrading-v7.html))
- Events are now split between "Meetings" and "AgendaItems"
- The new REST API for performant Linked Data resource fetching
- Documents are no longer nested under Events
- PDF documents are cached, so now it's possible to query from sources that had no support for this (such as iBabs)
- An `@context` json object was added in ElasticSearch for [RDF](https://www.w3.org/RDF/) / [JSON-LD](https://json-ld.org) compliance.
- A `discussed_at` field is added to AgendaItems and Documents.
- The available keys in the resources still adhere to Popolo where possible, so they have not changed.
- Text of extracted documents is now paginated, it's an array of pages.

## FAQ

### How is the data standardized?

Most of the ORI data follows the international [Popolo](https://www.popoloproject.com) specification.
We've added a couple of concepts, such as AgendaItems, which are namespaced under the Meeting ontology.
This Meeting ontology is a [work in progress](https://github.com/openstate/open-raadsinformatie/issues/127).
You can find all the defintions of the various models incudling the properties [here](https://github.com/openstate/open-raadsinformatie/tree/master/ocd_backend/models/definitions).

In the future, we hope to use the [VNG Open Raadsinformatie spec](https://github.com/VNG-Realisatie/Open-Raadsinformatie/) for serialization.

### Who uses ORI / these APIs?

- [OpenBesluitvorming.nl](https://openbesluitvorming.nl), the new search interface
- [1848.nl](https://1848.nl), which features a notification system (contact: Lucas Benschop)
- [WaarOverheid](https://waaroverheid.nl/), a location based app to navigate, search and subscribe to ORI data (contact: Alex Olieman)
- [Argu.co](https://argu.co), an e-democracy platform for civic engagement (contact: [Joep Meindertsma](mailto:joep@argu.co))
- [Raadstalk](https://www.vngrealisatie.nl/producten/raadstalk), a widget that shows trending topics that municipalities discuss. (contact: [Joep Meindertsma](mailto:joep@argu.co), [repo](https://github.com/ontola/raadstalk))
- Semantic Analysis of municipality data (contact: Robert Goené)
- Oberon Open Stateninformatie - Browser plugin (contact: Hans-Peter Harmsen)
- HierOverheid (in progress) (contact: Alex Olieman)
- Your app here? [Let us know](mailto:joep@ontola.io)!

### I have feedback / a different question

For technical questions, please create an issue in the aforementioned Github repos.
If you have general questions about Open Raadsinformatie, get in touch with project leader [Sander Bakker](mailto:sander.bakker@vng.nl).

### How can my municipality / government join?

If you're a Dutch municipality, fill in [this form](https://formulieren.vngrealisatie.nl/deelname_openraadsinformatie).
If you're another type of government, get in touch with [joep@argu.co](mailto:joep@argu.co)

### Who's behind this project?

Open Raadsinformatie and Open Stateninformatie were initiated by the [Open State Foundation](https://openstate.eu).
[VNG Realisatie](https://www.vngrealisatie.nl/producten/pilots-open-raadsinformatie) is the main funder.
[Ontola](https://ontola.io) / [Argu](https://argu.co) is responsible for the technology.
For more details, check out [poweredBy.tsx](https://github.com/ontola/openbesluitvorming/blob/master/front/src/poweredBy.tsx)

### Which projects does the API use?

- [Open Raadsinformatie](https://github.com/openstate/open-raadsinformatie/) for ETL & search
- [ori-theme-classifier](https://github.com/openstate/ori-theme-classifier) for adding themes
- [ori-api](https://github.com/ontola/ori_api/) for serializing to various RDF formats
