class ValidationError(Exception):
    pass


class RequiredProperty(Exception):
    pass


class MissingProperty(Exception):
    pass


class QueryResultError(Exception):
    pass


class SerializerNotFound(ValueError):
    pass


class SerializerError(Exception):
    pass
