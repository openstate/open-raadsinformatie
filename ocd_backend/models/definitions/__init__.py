from ocd_backend.models.namespace import Namespace

# Namespaces used in this project
FOAF = Namespace('http://xmlns.com/foaf/0.1/', 'foaf')
NCAL = Namespace('http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#', 'ncal')
OPENGOV = Namespace('http://www.w3.org/ns/opengov#', 'opengov')
ORG = Namespace('http://www.w3.org/ns/org#', 'org')
MEETING = Namespace('https://argu.co/ns/meeting/', 'meeting')
MAPPING = Namespace('https://argu.co/voc/mapping/', 'mapping')
META = Namespace('https://argu.co/ns/meta#', 'meta')
OWL = Namespace('http://www.w3.org/2002/07/owl#', 'owl')
PERSON = Namespace('http://www.w3.org/ns/person#', 'person')
SCHEMA = Namespace('http://schema.org/', 'schema')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#', 'rdfs')
DCTERMS = Namespace('http://purl.org/dc/terms/', 'dcterms')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#', 'skos')
BIO = Namespace('http://purl.org/vocab/bio/0.1/', 'bio')
BIBFRAME = Namespace('http://bibframe.org/vocab/', 'bibframe')
PROV = Namespace('https://www.w3.org/TR/2013/REC-prov-o-20130430/#', 'prov')
#IBABSTROEP = Namespace('https://argu.co/ns/opaque-model/ibabs#title')
ORI = Namespace('https://api.openraadsinformatie.nl/id/', 'ori')

ALL = [
    FOAF, NCAL, OPENGOV, ORG, MEETING, MAPPING, META, OWL, PERSON,
    SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME, PROV, ORI
]