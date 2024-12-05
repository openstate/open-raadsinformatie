from time import sleep
import redis

from ocd_backend.settings import REDIS_HOST, REDIS_PORT

class SharedAccess:
    """
    Provides a quick and dirty semaphore type of access accross multiple Celery workers.
    Usage:
         SharedAccess.acquire_lock(name)
             Call this at the start of code that should be synced across workers
         SharedAccess.release_lock(name)
             Call this at the end. If not called, the lock expires automatically after 10 seconds
    """

    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=2, decode_responses=True)

    @classmethod
    def acquire_lock(cls, name, expire_after=10):
        redis_key = cls._redis_key(name)

        acquired = cls._acquire_lock(redis_key, expire_after)

        while not acquired:
            sleep(0.1)
            acquired = cls._acquire_lock(redis_key, expire_after)

        return True

    @classmethod
    def release_lock(cls, name):
        redis_key = cls._redis_key(name)
        cls.redis_client.delete(redis_key)

    @classmethod
    def _redis_key(cls, name):
        return f'ori_shared_access_{name}'
    
    @classmethod
    def _acquire_lock(cls, redis_key, expire_after):
        acquired = cls.redis_client.setnx(redis_key, "1") == 1
        if acquired:
            cls.redis_client.expire(redis_key, expire_after)

        return acquired
