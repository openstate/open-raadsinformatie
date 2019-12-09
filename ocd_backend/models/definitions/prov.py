"""The classes in this org module are derived from and described by:
http://www.w3.org/ns/prov#
"""
import owl
from ocd_backend.models.definitions import Prov, Owl, Meeting
from ocd_backend.models.properties import StringProperty, DateTimeProperty


class Activity(Prov, owl.Thing):
    started_at_time = DateTimeProperty(Prov, 'startedAtTime')
    ended_at_time = DateTimeProperty(Prov, 'endedAtTime')
    used = StringProperty(Prov, 'used')
    generated = StringProperty(Prov, 'generated')
    had_primary_source = StringProperty(Prov, 'hadPrimarySource')
    same_as = StringProperty(Owl, 'sameAs')
    app_semver = StringProperty(Meeting, 'semver')
    external_identifier = StringProperty(Meeting, 'externalIdentifier')
