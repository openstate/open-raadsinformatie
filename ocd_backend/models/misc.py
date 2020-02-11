class Namespace:
    """A shortcut for defining a namespace with a prefix.

    Attributes:
        uri: The full uri of the namespace.
        prefix: Name of the prefix that will be used.
    """

    uri = None
    prefix = None

    def __str__(self):
        return self.prefix


class Uri:
    """A shortcut for constructing URI's as strings.

    Attributes:
        ns: The `Namespace` object prefix
        local_name: The part after the namespace

    Example:
        ```ori_identifier = Uri(Mapping, 'ori/identifier')```
    """

    def __new__(cls, ns, local_name):
        """Creates a full uri str with extra attributes"""
        assert issubclass(ns, Namespace)
        return '{}{}'.format(ns.uri, local_name)


class Url(str):
    """Serializes to a full URL to a linked property"""
    def __new__(cls, url):
        if not url:
            return None

        return super(Url, cls).__new__(cls, url)
