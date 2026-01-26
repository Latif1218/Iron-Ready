import os
import redis
from fastapi import Depends
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import SQLALCHEMY_DATABASE_URL


SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
seasionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

redis_client = None

def get_db():
    db = seasionlocal()
    try:
        yield db
    finally:
        db.close()
        
        
        
        
'''
# redis client to manage securly manage update-password endpoint (while user not authenticated)
def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
    return redis_client
'''

class RedisSession:
    """
    Singleton Redis client manager.
    Provides a single Redis connection pool for the entire application.
    """
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisSession, cls).__new__(cls)
            cls._instance._initialize_redis()
        return cls._instance
    
    def _initialize_redis(self):
        """Initialize Redis connection with connection pooling."""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_db = int(os.getenv("REDIS_DB", 0))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_username = os.getenv("REDIS_USERNAME", None)
        
        # Connection pool configuration
        pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            username=redis_username,
            max_connections=20,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        self._client = redis.Redis(connection_pool=pool)
        
        # Test connection
        try:
            self._client.ping()
            print(f"Redis connection established successfully to {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            raise
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        return self._client
    
    def get_key(self, pattern: str, *args) -> str:
        """
        Generate a consistent Redis key with optional arguments.
        
        Args:
            pattern: Key pattern (e.g., "password_reset:{email}:{code}")
            *args: Values to format into the pattern
        
        Returns:
            Formatted Redis key
        """
        return pattern.format(*args) if args else pattern
    
    def set_with_expiry(self, key: str, value: str, expiry_seconds: int = 600) -> bool:
        """
        Set a key-value pair with expiry.
        
        Args:
            key: Redis key
            value: Value to store
            expiry_seconds: Expiry time in seconds (default: 600 = 10 minutes)
        
        Returns:
            True if successful
        """
        return self._client.setex(key, expiry_seconds, value)
    
    def get(self, key: str) -> str:
        """
        Get value by key.
        
        Args:
            key: Redis key
        
        Returns:
            Value or None if key doesn't exist
        """
        return self._client.get(key)
    
    def delete(self, *keys) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
        
        Returns:
            Number of keys deleted
        """
        return self._client.delete(*keys)
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Redis key
        
        Returns:
            True if key exists
        """
        return self._client.exists(key) > 0
    
    def flush_all(self):
        """Flush all Redis data (use with caution!)."""
        self._client.flushall()
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            print("Redis connection closed")

# Dependency to get Redis session
def get_redis() -> RedisSession:
    """
    Dependency function to get Redis session.
    Returns the singleton RedisSession instance.
    """
    return RedisSession()

# Optional: Function to initialize Redis at startup
def init_redis():
    """
    Initialize Redis connection at application startup.
    Call this function in your main.py or startup event.
    """
    redis_session = RedisSession()
    return redis_session.client

# Health check functions
def check_database_health():
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def check_redis_health():
    """Check if Redis connection is healthy."""
    try:
        redis_session = RedisSession()
        return redis_session.client.ping()
    except Exception as e:
        print(f"Redis health check failed: {e}")
        return False