"""
Simple script to test MongoDB connection.
"""

import os
import sys
import subprocess
from pathlib import Path

def start_mongodb():
    """Start MongoDB server"""
    print("Starting MongoDB server...")
    
    try:
        # Try to start MongoDB directly
        subprocess.run(["mongod", "--dbpath", "mongodb_data"], 
                      check=False, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("MongoDB server started successfully")
        return True
    except Exception as e:
        print(f"Error starting MongoDB server: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    
    try:
        # Try to import pymongo
        import pymongo
        print("Successfully imported pymongo")
        
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        
        # List databases
        print("Available databases:")
        for db in client.list_database_names():
            print(f"- {db}")
        
        # Create a test database
        db = client["test_db"]
        
        # Create a test collection
        collection = db["test_collection"]
        
        # Insert a test document
        test_doc = {"name": "Test", "value": 123}
        result = collection.insert_one(test_doc)
        print(f"Inserted document with ID: {result.inserted_id}")
        
        # Find the document
        found_doc = collection.find_one({"name": "Test"})
        print(f"Found document: {found_doc}")
        
        # Delete the document
        delete_result = collection.delete_one({"name": "Test"})
        print(f"Deleted {delete_result.deleted_count} document(s)")
        
        print("MongoDB connection test successful!")
        return True
    except ImportError:
        print("Failed to import pymongo. Make sure it's installed.")
        print("Run 'pip install pymongo' to install it.")
        return False
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return False

if __name__ == "__main__":
    test_mongodb_connection()
