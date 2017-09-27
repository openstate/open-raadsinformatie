import owl
from .namespaces import FOAF
from owltology.property import Type


class Agent(owl.Thing):
    _type = Type(FOAF)


class Group(Agent):
    _type = Type(FOAF)
