from ocd_backend.models.misc import Namespace


# Namespaces used in this project


class Foaf(Namespace):
    uri = 'http://xmlns.com/foaf/0.1/'
    prefix = 'foaf'


class Ncal(Namespace):
    uri = 'http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#'
    prefix = 'ncal'


class Opengov(Namespace):
    uri = 'http://www.w3.org/ns/opengov#'
    prefix = 'opengov'


class Org(Namespace):
    uri = 'http://www.w3.org/ns/org#'
    prefix = 'org'


class Meeting(Namespace):
    uri = 'https://argu.co/ns/meeting/'
    prefix = 'meeting'


class Mapping(Namespace):
    uri = 'https://argu.co/voc/mapping/'
    prefix = 'mapping'


class Meta(Namespace):
    uri = 'https://argu.co/ns/meta#'
    prefix = 'meta'


class Owl(Namespace):
    uri = 'http://www.w3.org/2002/07/owl#'
    prefix = 'owl'


class Person(Namespace):
    uri = 'http://www.w3.org/ns/person#'
    prefix = 'person'


class Schema(Namespace):
    uri = 'http://schema.org/'
    prefix = 'schema'


class Rdf(Namespace):
    uri = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    prefix = 'rdf'


class Rdfs(Namespace):
    uri = 'http://www.w3.org/2000/01/rdf-schema#'
    prefix = 'rdfs'


class Dcterms(Namespace):
    uri = 'http://purl.org/dc/terms/'
    prefix = 'dcterms'


class Skos(Namespace):
    uri = 'http://www.w3.org/2004/02/skos/core#'
    prefix = 'skos'


class Bio(Namespace):
    uri = 'http://purl.org/vocab/bio/0.1/'
    prefix = 'bio'


class Bibframe(Namespace):
    uri = 'http://bibframe.org/vocab/'
    prefix = 'bibframe'


class Prov(Namespace):
    uri = 'http://www.w3.org/ns/prov#'
    prefix = 'prov'


class Pav(Namespace):
    uri = 'http://purl.org/pav/'
    prefix = 'pav'


class Ori(Namespace):
    uri = 'https://id.openraadsinformatie.nl/'
    prefix = 'ori'


class Dbo(Namespace):
    uri = 'http://dbpedia.org/ontology/'
    prefix = 'dbo'


# class Opaque(Namespace):
#     uri = 'https://argu.co/ns/opaque-model/'
#     prefix = 'opaque'


ALL = [
    Foaf, Ncal, Opengov, Org, Meeting, Mapping, Meta, Owl, Person,
    Schema, Rdf, Rdfs, Dcterms, Skos, Bio, Bibframe, Prov, Ori
]
