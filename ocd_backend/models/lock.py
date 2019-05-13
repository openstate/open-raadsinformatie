import time
import string
import random

from ocd_backend import celery_app

redis = celery_app.backend.client
lock_prefix = 'lock_'
lock_expiry_seconds = 10
lock_max_seconds = 6000


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
        before_lock_value = redis.get(self.lock_identifier)

        wait_delta = timeout
        while time.time() < time.time() + wait_delta:
            if redis.set(self.lock_identifier, self.random_value, ex=lock_expiry_seconds, nx=True):
                return True
            else:
                current_lock_value = redis.get(self.lock_identifier)
                if before_lock_value and before_lock_value != current_lock_value:
                    if wait_delta > lock_max_seconds:
                        break
                    wait_delta += timeout
                    before_lock_value = current_lock_value
                time.sleep(random.uniform(0.01, 0.1))

        raise AcquireTimeoutException('Lock acquire failed, waited for %s seconds' % wait_delta)

    def release(self):
        lock_value = redis.get(self.lock_identifier)
        if lock_value == self.random_value:
            redis.delete(self.lock_identifier)

    @staticmethod
    def random_generator(size=20, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
