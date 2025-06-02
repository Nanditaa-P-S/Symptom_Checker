"""
Script to migrate data from local JSON storage to MongoDB.
This script reads all data from the local_data directory and inserts it into MongoDB.
"""

import os
import sys
import json
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'symptom_checker.settings')
django.setup()

from django.conf import settings

from checker.mongo_utils import get_mongo_client
from checker.local_storage import get_local_storage

def migrate_collection(collection_name):
    """Migrate a single collection from local storage to MongoDB"""
    print(f"Migrating collection: {collection_name}")

    # Get local storage and MongoDB client
    local_storage = get_local_storage()
    mongo_client = get_mongo_client()

    # Get all documents from local storage
    local_docs = local_storage.find(collection_name)

    if not local_docs:
        print(f"No documents found in local storage for collection: {collection_name}")
        return 0

    print(f"Found {len(local_docs)} documents in local storage")

    # Insert documents into MongoDB
    migrated_count = 0
    for doc in local_docs:
        # Convert 'id' to '_id' for MongoDB
        if 'id' in doc and '_id' not in doc:
            doc['_id'] = doc['id']

        # Convert 'timestamp' to '_timestamp' for MongoDB
        if 'timestamp' in doc and '_timestamp' not in doc:
            doc['_timestamp'] = doc['timestamp']

        try:
            # Insert into MongoDB
            result = mongo_client.insert_one(collection_name, doc)
            if result:
                migrated_count += 1
        except Exception as e:
            print(f"Error inserting document: {e}")

    print(f"Successfully migrated {migrated_count} documents to MongoDB")
    return migrated_count

def get_collection_names():
    """Get all collection names from local storage directory"""
    local_storage = get_local_storage()
    data_dir = local_storage.data_dir

    collection_names = []
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                collection_name = filename[:-5]  # Remove .json extension
                collection_names.append(collection_name)

    return collection_names

def main():
    """Main function to migrate all data from local storage to MongoDB"""
    print("Starting migration from local storage to MongoDB...")

    # Start MongoDB server
    try:
        import subprocess
        print("Starting MongoDB server...")
        subprocess.run(["python", "manage.py", "start_mongodb"], check=True)
    except Exception as e:
        print(f"Error starting MongoDB server: {e}")

    # Get MongoDB client and check connection
    mongo_client = get_mongo_client()
    # Force reconnection
    if not mongo_client.connect():
        print("Failed to connect to MongoDB. Make sure MongoDB is running.")
        print("Run 'python manage.py start_mongodb' to start MongoDB.")
        return

    # Get all collection names
    collection_names = get_collection_names()

    if not collection_names:
        print("No collections found in local storage.")
        return

    print(f"Found {len(collection_names)} collections: {', '.join(collection_names)}")

    # Migrate each collection
    total_migrated = 0
    for collection_name in collection_names:
        migrated = migrate_collection(collection_name)
        total_migrated += migrated

    print(f"Migration complete. Total documents migrated: {total_migrated}")

if __name__ == "__main__":
    main()
