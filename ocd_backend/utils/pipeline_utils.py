import os
import redis

from ocd_backend.settings import REDIS_HOST, REDIS_PORT

class PipelineUtils:
  redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

  def is_locked(self, lock_key):
    return not(not self.lock_value(lock_key))
  
  def lock_value(self, lock_key):
    return self.redis_client.get(lock_key)

  def claim_lock(self, lock_key, source):
    self.redis_client.set(lock_key, source)

  def release_lock(self, lock_key):
    self.redis_client.delete(lock_key)

  # The source value sometimes differs from the key value, causing the lock key not to be released in the end.
  # Update lock if key differs from source
  def update_lock(self, lock_key, source, full_source_key):
    if source == full_source_key:
      return # Nothing to be done

    if self.lock_value(lock_key) != source:
      return # Only update lock if currently stored value equals source

    self.claim_lock(lock_key, full_source_key)

  def is_maintenance(self, maintenance_file):
    return os.path.exists(maintenance_file)