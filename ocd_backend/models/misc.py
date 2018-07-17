class Namespace(object):
    """A shortcut for defining a namespace with a prefix.

    Attributes:
        namespace: The full uri of the namespace.
        prefix: Name of the prefix that will be used.

    Example:
        ```MAPPING = Namespace('https://argu.co/voc/mapping/', 'mapping')```
    """

    def __init__(self, namespace, prefix):
        self.namespace = namespace
        self.prefix = prefix

    def __str__(self):
        return self.prefix


class URI(str):
    """A shortcut for writing full URI's.

    Attributes:
        ns: The `Namespace` object prefix
        local_name: The part after the namespace

    Example:
        ```ori_identifier = URI(MAPPING, 'ori/identifier')```
    """

    def __new__(cls, ns, local_name):
        """Creates a full uri str with extra attributes"""
        assert type(ns) == Namespace
        cls.ns = ns
        cls.local_name = local_name
        return super(URI, cls).__new__(cls, '{}{}'.format(cls.ns.namespace,
                                                          cls.local_name))

    def __init__(self, ns, local_name):
        """Just here to match the signature"""
        super(URI, self).__init__()
