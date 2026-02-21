import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_mongo_client():
    """
    Create and return MongoDB client using MONGODB_URL from environment.
    """
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable not set")
    
    return MongoClient(mongodb_url)