import os

import redis


REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_connection = redis.from_url(REDIS_URL)
