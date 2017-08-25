from ocd_backend.models import foaf

NAMESPACE = 'person'


class Person(foaf.Agent):
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
