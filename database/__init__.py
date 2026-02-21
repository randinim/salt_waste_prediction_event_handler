from .connection import get_mongo_client

# Create connection on startup
client = get_mongo_client()