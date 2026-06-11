from flask_caching import Cache

# SimpleCache instance used across the project
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
