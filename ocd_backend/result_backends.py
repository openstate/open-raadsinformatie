from celery.backends.redis import RedisBackend


class OCDBackendMixin:
    """
    This mixin defines the methods that we expect the result backend to
    implement. We use this to make sure the backend that is used supports the
    functionality that we require for the ETL pipeline.

    You should subclass one of Celery's backend classes, and add this mixin
    **after** the class definition. For example:

        from celery.backends.cassandra import CassandraBackend

        class MyOCDBackend(CassandraBackend, OCDBackendMixin):

            implements_incr = True

            def incr(self, key):
                # implementation of incr on Cassandra backend

    This will make sure whether the subclass has implemented all the required
    methods, and allow it to override specific methods if required.
    """

    def get(self, key):
        """Get value by `key`"""
        raise NotImplementedError('Subclass should implement `get` method')

    def set(self, key, value):
        """Set `key` to `value`"""
        raise NotImplementedError('Subclass should implement `get` method')

    def remove(self, key):
        """Remove `key`"""
        raise NotImplementedError('Subclass should implement `remove` method')

    def add_value_to_set(self, set_name, value):
        """Add `value` to `set_name`"""
        raise NotImplementedError('Subclass should implement `add_to_set` '
                                  'method')

    def remove_value_from_set(self, set_name, value):
        """Remove `value` from `set_name`"""
        raise NotImplementedError('Subclass should implement `remove_value_fro'
                                  'm_set` method')

    def get_set_cardinality(self, set_name):
        """Get the number of values stored in `set_name`"""
        raise NotImplementedError('Subclass should implement `get_set_cardinal'
                                  'ity` method')

    def update_ttl(self, key, ttl=300):
        """Extend the TTL of `key` with `ttl` seconds"""


class OCDRedisBackend(RedisBackend, OCDBackendMixin):
    def add_value_to_set(self, set_name, value):
        self.client.sadd(set_name, value)

    def remove_value_from_set(self, set_name, value):
        self.client.srem(set_name, value)

    def get_set_cardinality(self, set_name):
        return self.client.scard(set_name)

    def get_set_members(self, set_name):
        return self.client.smembers(set_name)

    def remove(self, key):
        return self.client.delete(key)

    def update_ttl(self, key, ttl=300):
        return self.client.expire(key, ttl)

    def increment(self, key):
        return self.client.incr(key)
