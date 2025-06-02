"""
Direct MongoDB connection script.
This script connects directly to MongoDB and migrates data from local storage.
"""

import os
import json
import datetime
import subprocess
import sys
from pathlib import Path

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Directory to store MongoDB data files
DATA_DIR = os.path.join(BASE_DIR, 'mongodb_data')
LOG_DIR = os.path.join(BASE_DIR, 'mongodb_logs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Local data directory
LOCAL_DATA_DIR = os.path.join(BASE_DIR, 'local_data')

def start_mongodb():
    """Start MongoDB server"""
    print("Starting MongoDB server...")
    
    # Start MongoDB using the management command
    try:
        subprocess.run([sys.executable, "manage.py", "start_mongodb"], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("MongoDB server started successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting MongoDB server: {e}")
        print(f"Error output: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"Error starting MongoDB server: {e}")
        return False

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

def migrate_to_mongodb():
    """Migrate data from local storage to MongoDB"""
    print("Starting migration from local storage to MongoDB...")
    
    # Start MongoDB server
    if not start_mongodb():
        print("Failed to start MongoDB server. Exiting.")
        return
    
    # Try to import pymongo
    try:
        from pymongo import MongoClient
        print("Successfully imported pymongo")
    except ImportError:
        print("Failed to import pymongo. Make sure it's installed.")
        print("Run 'pip install pymongo' to install it.")
        return
    
    # Connect to MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["symptom_checker_db"]
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
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
        print(f"Migrating collection: {collection_name}")
        
        # Get data from local storage
        local_docs = get_local_data(collection_name)
        
        if not local_docs:
            print(f"No documents found in local storage for collection: {collection_name}")
            continue
        
        print(f"Found {len(local_docs)} documents in local storage")
        
        # Get MongoDB collection
        collection = db[collection_name]
        
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
                result = collection.insert_one(doc)
                if result.inserted_id:
                    migrated_count += 1
            except Exception as e:
                print(f"Error inserting document: {e}")
        
        print(f"Successfully migrated {migrated_count} documents to MongoDB")
        total_migrated += migrated_count
    
    print(f"Migration complete. Total documents migrated: {total_migrated}")

if __name__ == "__main__":
    migrate_to_mongodb()
