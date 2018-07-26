class Namespace(object):
    """A shortcut for defining a namespace with a prefix.

    Attributes:
        uri: The full uri of the namespace.
        prefix: Name of the prefix that will be used.
    """

    uri = None
    prefix = None

    def __str__(self):
        return self.prefix


class Uri(str):
    """A shortcut for writing full URI's.

    Attributes:
        ns: The `Namespace` object prefix
        local_name: The part after the namespace

    Example:
        ```ori_identifier = Uri(Mapping, 'ori/identifier')```
    """

    def __new__(cls, ns, local_name):
        """Creates a full uri str with extra attributes"""
        assert issubclass(ns, Namespace)
        cls.ns = ns
        cls.local_name = local_name
        return super(Uri, cls).__new__(cls, '{}{}'.format(ns.uri,
                                                          cls.local_name))

    def __init__(self, ns, local_name):
        """Just here to match the signature"""
        super(Uri, self).__init__()
