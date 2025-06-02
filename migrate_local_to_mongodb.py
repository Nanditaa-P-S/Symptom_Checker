"""
Script to migrate data from local JSON storage to MongoDB.
"""

import os
import json
import datetime
from pathlib import Path

# Import pymongo
import pymongo

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Local data directory
LOCAL_DATA_DIR = os.path.join(BASE_DIR, 'local_data')

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["symptom_checker_db"]

def json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)

def get_local_data(collection_name):
    """Get data from local storage"""
    file_path = os.path.join(LOCAL_DATA_DIR, f"{collection_name}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading collection {collection_name}: {e}")
            return []
    return []

def get_collection_names():
    """Get all collection names from local storage directory"""
    collection_names = []
    if os.path.exists(LOCAL_DATA_DIR):
        for filename in os.listdir(LOCAL_DATA_DIR):
            if filename.endswith('.json'):
                collection_name = filename[:-5]  # Remove .json extension
                collection_names.append(collection_name)
    
    return collection_names

def migrate_collection(collection_name):
    """Migrate a single collection from local storage to MongoDB"""
    print(f"Migrating collection: {collection_name}")
    
    # Get data from local storage
    local_docs = get_local_data(collection_name)
    
    if not local_docs:
        print(f"No documents found in local storage for collection: {collection_name}")
        return 0
    
    print(f"Found {len(local_docs)} documents in local storage")
    
    # Get MongoDB collection
    collection = db[collection_name]
    
    # Insert documents into MongoDB
    migrated_count = 0
    for doc in local_docs:
        try:
            # Convert 'id' to '_id' for MongoDB
            if 'id' in doc and '_id' not in doc:
                doc['_id'] = doc['id']
                del doc['id']
            
            # Convert 'timestamp' to '_timestamp' for MongoDB
            if 'timestamp' in doc and '_timestamp' not in doc:
                doc['_timestamp'] = doc['timestamp']
                del doc['timestamp']
            
            # Insert into MongoDB
            result = collection.insert_one(doc)
            if result.inserted_id:
                migrated_count += 1
        except pymongo.errors.DuplicateKeyError:
            print(f"Document with ID {doc.get('_id')} already exists in MongoDB")
        except Exception as e:
            print(f"Error inserting document: {e}")
    
    print(f"Successfully migrated {migrated_count} documents to MongoDB")
    return migrated_count

def main():
    """Main function to migrate all data from local storage to MongoDB"""
    print("Starting migration from local storage to MongoDB...")
    
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
