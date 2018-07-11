class Namespace(object):
    def __init__(self, namespace, prefix):
        self.namespace = namespace
        self.prefix = prefix

    def __str__(self):
        return self.prefix


class URI(str):
    def __new__(self, ns, local_name):
        self.ns = ns
        self.local_name = local_name
        return super(URI, self).__new__(self, '%s%s' % (self.ns.namespace, self.local_name))
