import foaf
from .namespaces import PERSON


class Person(foaf.Agent):
    NAMESPACE = PERSON
    name = 'foaf:name'
    givenName = 'foaf:givenName'
    familyName = 'foaf:familyName'
    gender = 'foaf:gender'
    birthDate = 'schema:birthDate'
    deathDate = 'schema:deathDate'
    email = 'schema:email'
    nationalIdentity = 'opengov:nationalIdentity'
    image = 'schema:image'
    seeAlso = 'rdfs:seeAlso'
