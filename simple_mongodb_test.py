"""
Very simple script to test MongoDB connection.
"""

try:
    print("Trying to import pymongo...")
    import pymongo
    print("Successfully imported pymongo")
    
    print("Trying to connect to MongoDB...")
    client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    
    print("Pinging MongoDB server...")
    client.admin.command('ping')
    
    print("MongoDB connection successful!")
    
    print("Available databases:")
    for db in client.list_database_names():
        print(f"- {db}")
    
except ImportError as e:
    print(f"Failed to import pymongo: {e}")
    print("Make sure pymongo is installed with: pip install pymongo")
except Exception as e:
    print(f"MongoDB connection error: {e}")
