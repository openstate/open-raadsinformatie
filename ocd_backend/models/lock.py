import time
import string
import random

from ocd_backend import celery_app

redis = celery_app.backend.client
lock_prefix = 'lock_'
lock_expiry_seconds = 10


class AcquireTimeoutException(Exception):
    pass


class Lock(object):
    random_value = None

    def __init__(self, identifier):
        self.lock_identifier = '%s%s' % (lock_prefix, identifier)

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self, timeout=lock_expiry_seconds):
        self.random_value = self.random_generator()

        end = time.time() + timeout
        while time.time() < end:
            if redis.set(self.lock_identifier, self.random_value, ex=lock_expiry_seconds, nx=True):
                return True
            else:
                time.sleep(random.uniform(0.01, 0.1))

        raise AcquireTimeoutException('Lock acquire failed, waited for %s seconds', lock_expiry_seconds)

    def release(self):
        lock_value = redis.get(self.lock_identifier)
        if lock_value == self.random_value:
            redis.delete(self.lock_identifier)

    @staticmethod
    def random_generator(size=20, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
