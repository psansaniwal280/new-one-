import json
import sys
from datetime import timedelta
import pickle
import httpx
import redis
import os
import urllib.parse


def redis_connect() -> redis.client.Redis:
    """
        Heroku - Redis Connection 
    """
    # try:
    #     redis_url = os.getenv('REDISTOGO_URL')
    #     urllib.parse.uses_netloc.append('redis')
    #     url = urllib.parse.urlparse(redis_url)  
    #     print(url.hostname)      
    #     client = redis.Redis(host=url.hostname, port=url.port, db=0, password=url.password)
    #     ping = client.ping()
    #     if ping is True:
    #         return client
    # except redis.AuthenticationError:
    #     print("AuthenticationError")
    #     sys.exit(1)
    """
        lOCAHOST - Redis Connection
    """
    try:
        client = redis.Redis(
            host="127.0.0.1",
            port=6379
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        print("AuthenticationError")
        sys.exit(1)


# client = redis_connect()


def get_routes_from_api(client, coordinates: str) -> dict:
    """Data from mapbox api."""

    with httpx.Client() as client:
        base_url = "https://api.mapbox.com/optimized-trips/v1/mapbox/driving"

        geometries = "geojson"
        access_token = "Your-MapBox-API-token"

        url = f"{base_url}/{coordinates}?geometries={geometries}&access_token={access_token}"

        response = client.get(url)
        return response.json()


def get_routes_from_cache(client, key: str) -> str:
    """Data from redis."""

    val = client.get(key)
    return val


def set_routes_to_cache(client, key: str, value: str) -> bool:
    """Data to redis."""

    state = client.setex(key, timedelta(seconds=1200), value=value, )
    return state


def get_hashmap_from_cache(client, key):
    """Data from redis as hashmap/dictionary"""
    if client.get(key):
        val = client.get(key)
        return pickle.loads(val)


def set_hashmap_to_cache(client, key, value):
    """Data to redis as hashmap/dictionary """
    print(value)
    state = client.set(key, pickle.dumps(value))
    return state


def delete_hashmap_from_cache(client, rootKey, key):
    val = client.get(rootKey)
    val = pickle.loads(val)
    value = val.delete(key)
    state = client.set(rootKey, pickle.dumps(value))
    return state


def delete_routes_from_cache(client, key: str):
    """Delete Data from Redis"""

    state = client.delete(key)

    return state


def clear_redis(client):
    """"Clear everything in redis"""

    state = client.flushdb()
    return state
