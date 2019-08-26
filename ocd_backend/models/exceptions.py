class ValidationError(ValueError):
    """Error thrown when a value does not appear valid for a given propery."""
    pass


class MissingProperty(ValueError):
    """Thrown when a property should be present but is not there."""
    pass


class RequiredProperty(Exception):
    """Thrown when a property is required but the value is empty."""
    pass


class IgnoredProperty(Exception):
    """Thrown when a property is ignored by ignore_for_loader"""
    pass


class QueryResultError(Exception):
    """Error thrown when the query yields unexpected results."""
    pass


class QueryEmptyResult(Exception):
    """Error thrown when the query yields no results"""


class SerializerNotFound(Exception):
    """Thrown when a specific serializer could not be found."""
    pass


class SerializerError(Exception):
    """Error thrown when a model could not be serialized."""
    pass
