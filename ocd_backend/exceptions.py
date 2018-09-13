class ConfigurationError(Exception):
    """Thrown when a setting in sources.json is missing or has
    an improper value."""


class NotFound(Exception):
    """Indicates that a requested item does not exist."""


class UnableToGenerateObjectId(Exception):
    """Indicates that the 'object_id' can't be generated."""


class NoDeserializerAvailable(Exception):
    """Thrown when there is no deserializer available for the
    content-type of an."""


class FieldNotAvailable(Exception):
    """Exception thrown when a field could not be found."""

    def __init__(self, field):
        self.field = field

    def __str__(self):
        return repr(self.field)


class SkipEnrichment(Exception):
    """Exception thrown from within an enrichment task to indicate that
    there is a valid reason for skipping the enrichemnt."""


class UnsupportedContentType(Exception):
    """Exception thrown when a task is asked to process media content
    that is doesn't understand."""


class MissingTemplateTag(KeyError):
    """Thrown when a template tag is missing in the configuration"""


class InvalidDatetime(ValueError):
    pass


class InvalidFile(OSError):
    """Exception thrown when a file on the filesystem is corrupted
    or does not seem correct"""


class ItemAlreadyProcessed(Exception):
    """Item has been processed earlier and should not be processed again.
    This should be overriden by 'force_old_files' in source_definition, for
    example when everything must be reprocessed."""
