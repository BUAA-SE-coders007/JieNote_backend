import redis
import time
import os

redis_client = None  # 全局 Redis 客户端变量

def get_redis_client():
    """
    初始化并返回 Redis 客户端。
    如果 Redis 客户端已存在，则直接返回。
    """
    global redis_client
    if redis_client is None:
        while True:
            try:
                print("Connecting to Redis...")
                redis_client = redis.StrictRedis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    password=os.getenv("REDIS_PASSWORD", None), 
                    db=0,
                    decode_responses=True
                )
                redis_client.ping()
                print("Connected to Redis successfully.")
                break
            except redis.ConnectionError:
                print("Redis connection failed, retrying...")
                time.sleep(1)
    return redis_client
