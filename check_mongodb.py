"""
Simple script to check if MongoDB is working.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'symptom_checker.settings')
django.setup()

from pymongo import MongoClient

def main():
    """Check if MongoDB is working"""
    print("Checking MongoDB connection...")
    
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        
        # Check connection
        client.admin.command('ping')
        
        print("MongoDB connection successful!")
        
        # List databases
        print("Available databases:")
        for db in client.list_database_names():
            print(f"- {db}")
        
        # Use symptom_checker_db
        db = client["symptom_checker_db"]
        
        # List collections
        print("\nCollections in symptom_checker_db:")
        for collection in db.list_collection_names():
            print(f"- {collection}")
            # Count documents
            count = db[collection].count_documents({})
            print(f"  Documents: {count}")
        
        return True
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return False

if __name__ == "__main__":
    main()
