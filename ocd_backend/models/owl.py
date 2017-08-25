NAMESPACE = 'owl'


class Metaclass(type):
    def __new__(meta, name, bases, dct):
        dct.setdefault('type', '%s:%s' % (NAMESPACE, name))
        return super(Metaclass, meta).__new__(meta, name, bases, dct)


class Thing(object):
    __metaclass__ = Metaclass

    # Optional local identifier which doesn't have to be an URI
    identifier = 'dcterms:identifier'
