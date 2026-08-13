import environ
import redis

env = environ.Env()


def test_redis_connection_is_reachable():
    client = redis.Redis.from_url(env("REDIS_URL", default="redis://localhost:6379/0"))
    assert client.ping() is True
