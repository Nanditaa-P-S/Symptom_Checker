import datetime
import os
from django.conf import settings
from .local_storage import get_local_storage


# Try to import MongoDB modules, but make them optional
try:
    from pymongo import MongoClient
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    # Create dummy classes for when MongoDB is not available
    class MongoClient:
        def __init__(self, *args, **kwargs):
            pass
    class ObjectId:
        def __init__(self, *args, **kwargs):
            pass

class MongoDBClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Check if MongoDB is available
        if not MONGODB_AVAILABLE:
            print("MongoDB is not available. Install pymongo and bson packages to use MongoDB features.")
            self.client = None
            self.db = None
            return

        # Set up paths for local MongoDB storage
        import os
        from django.conf import settings

        # Set database name
        self.db_name = "symptom_checker_db"

        # Set local data directory path for MongoDB data files
        self.data_dir = os.path.join(settings.BASE_DIR, 'mongodb_data')

        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                print(f"Created MongoDB data directory at {self.data_dir}")
            except Exception as e:
                print(f"Failed to create MongoDB data directory: {e}")

        # Use MongoDB's local storage mode
        # For MongoDB Community Edition
        self.connection_string = "mongodb://localhost:27017/"

        # Initialize client and db
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        if not MONGODB_AVAILABLE:
            return False

        # Try to start the local MongoDB server
        try:
            import sys
            import subprocess
            import os
            from django.conf import settings

            # Path to the start_local_mongodb.py script
            script_path = os.path.join(settings.BASE_DIR, 'start_local_mongodb.py')

            # Start the local MongoDB server
            if os.path.exists(script_path):
                print("Starting local MongoDB server...")
                subprocess.Popen([sys.executable, script_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Error starting local MongoDB server: {e}")

        # Connect to MongoDB using direct connection string
        try:
            # Use a direct connection approach without relying on JSON
            connection_options = {
                'serverSelectionTimeoutMS': 5000,
                'directConnection': True,
                'retryWrites': True,
                'w': 'majority'
            }
            self.client = MongoClient(self.connection_string, **connection_options)

            # Test the connection with a simple command
            self.client.admin.command('ping')

            # Get database
            self.db = self.client[self.db_name]
            print("MongoDB connection successful")
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            return False

    def get_collection(self, collection_name):
        if not MONGODB_AVAILABLE:
            return None

        if self.db is None:
            if not self.connect():
                return None
        return self.db[collection_name]

    def insert_one(self, collection_name, document):
        # Always store in local storage as backup
        local_storage = get_local_storage()

        # Create a copy of the document for local storage
        local_doc = document.copy()

        # Convert _id to id for local storage if present
        if '_id' in local_doc:
            local_doc['id'] = str(local_doc.pop('_id'))

        local_id = local_storage.insert_one(collection_name, local_doc)

        if not MONGODB_AVAILABLE:
            return local_id

        try:
            collection = self.get_collection(collection_name)
            if collection:
                result = collection.insert_one(document)
                return result.inserted_id
            return local_id
        except Exception as e:
            print(f"MongoDB insert_one error: {e}")
            return local_id

    def insert_many(self, collection_name, documents):
        # Always store in local storage as backup
        local_storage = get_local_storage()
        local_ids = []

        # Copy documents to avoid modifying the original
        documents_copy = [doc.copy() for doc in documents]

        # Insert each document into local storage
        for doc in documents_copy:
            # Convert _id to id for local storage if present
            if '_id' in doc:
                doc['id'] = str(doc.pop('_id'))

            local_id = local_storage.insert_one(collection_name, doc)
            local_ids.append(local_id)

        if not MONGODB_AVAILABLE:
            return local_ids

        try:
            collection = self.get_collection(collection_name)
            if collection:
                result = collection.insert_many(documents)
                return result.inserted_ids
            return local_ids
        except Exception as e:
            print(f"MongoDB insert_many error: {e}")
            return local_ids

    def find_one(self, collection_name, query):
        # Always try local storage first or as fallback
        local_storage = get_local_storage()

        if not MONGODB_AVAILABLE:
            return local_storage.find_one(collection_name, query)

        try:
            collection = self.get_collection(collection_name)
            if collection is not None:
                mongo_result = collection.find_one(query)
                if mongo_result:
                    # Convert MongoDB result to match local storage format
                    if '_id' in mongo_result:
                        mongo_result['id'] = str(mongo_result['_id'])
                    if '_timestamp' in mongo_result:
                        mongo_result['timestamp'] = mongo_result['_timestamp']
                    return mongo_result
                # If no result from MongoDB, try local storage
                return local_storage.find_one(collection_name, query)
            return local_storage.find_one(collection_name, query)
        except Exception as e:
            print(f"MongoDB find_one error: {e}")
            # Fallback to local storage
            return local_storage.find_one(collection_name, query)

    def find(self, collection_name, query=None, projection=None):
        # Always try local storage first or as fallback
        local_storage = get_local_storage()

        if not MONGODB_AVAILABLE:
            return local_storage.find(collection_name, query)

        try:
            collection = self.get_collection(collection_name)
            if collection is not None:
                mongo_results = list(collection.find(query or {}, projection))

                # Convert MongoDB results to match local storage format
                for doc in mongo_results:
                    if '_id' in doc:
                        doc['id'] = str(doc['_id'])
                    if '_timestamp' in doc:
                        doc['timestamp'] = doc['_timestamp']

                if mongo_results:
                    return mongo_results
                # If no results from MongoDB, try local storage
                return local_storage.find(collection_name, query)
            return local_storage.find(collection_name, query)
        except Exception as e:
            print(f"MongoDB find error: {e}")
            # Fallback to local storage
            return local_storage.find(collection_name, query)

    def update_one(self, collection_name, query, update):
        # Always update local storage
        local_storage = get_local_storage()
        local_result = local_storage.update_one(collection_name, query, update)

        if not MONGODB_AVAILABLE:
            return local_result

        try:
            collection = self.get_collection(collection_name)
            if collection:
                # Create a proper update document without using $set
                # First find the document
                doc = collection.find_one(query)
                if doc:
                    # Update the document fields
                    for key, value in update.items():
                        doc[key] = value
                    # Replace the entire document
                    mongo_result = collection.replace_one({"_id": doc["_id"]}, doc)
                    return mongo_result
                else:
                    # Document not found
                    return local_result
            return local_result
        except Exception as e:
            print(f"MongoDB update_one error: {e}")
            return local_result

    def delete_one(self, collection_name, query):
        # Always delete from local storage
        local_storage = get_local_storage()
        local_result = local_storage.delete_one(collection_name, query)

        if not MONGODB_AVAILABLE:
            return local_result

        try:
            collection = self.get_collection(collection_name)
            if collection:
                mongo_result = collection.delete_one(query)
                return mongo_result
            return local_result
        except Exception as e:
            print(f"MongoDB delete_one error: {e}")
            return local_result

    def close(self):
        if not MONGODB_AVAILABLE:
            return

        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Helper functions for converting between Django models and MongoDB documents
def model_to_dict(instance):
    """Convert a Django model instance to a dictionary for MongoDB"""
    if not MONGODB_AVAILABLE:
        return {}

    data = {}
    for field in instance._meta.fields:
        field_name = field.name
        field_value = getattr(instance, field_name)
        data[field_name] = field_value

    # Handle many-to-many fields
    for field in instance._meta.many_to_many:
        field_name = field.name
        related_objects = getattr(instance, field_name).all()
        data[field_name] = [model_to_dict(obj) for obj in related_objects]

    return data

# Get MongoDB client instance
def get_mongo_client():
    return MongoDBClient.get_instance()
