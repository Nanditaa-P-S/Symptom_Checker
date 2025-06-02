import os
import json
import datetime
from django.conf import settings

class LocalStorage:
    """
    Utility class for storing data locally in JSON files
    when MongoDB is not available or as a backup
    """

    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(settings.BASE_DIR, 'local_data')
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                print(f"Created local data directory at {self.data_dir}")
            except Exception as e:
                print(f"Failed to create local data directory: {e}")

    def _get_collection_path(self, collection_name):
        """Get the file path for a collection"""
        return os.path.join(self.data_dir, f"{collection_name}.json")

    def _load_collection(self, collection_name):
        """Load data from a collection file"""
        file_path = self._get_collection_path(collection_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading collection {collection_name}: {e}")
                return []
        return []

    def _save_collection(self, collection_name, data):
        """Save data to a collection file"""
        file_path = self._get_collection_path(collection_name)
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            return True
        except Exception as e:
            print(f"Error saving collection {collection_name}: {e}")
            return False

    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return str(obj)

    def insert_one(self, collection_name, document):
        """Insert a document into a collection"""
        data = self._load_collection(collection_name)

        # Add ID if not present (without leading underscore)
        if 'id' not in document:
            document['id'] = str(len(data) + 1)

        # Add timestamp (without leading underscore)
        document['timestamp'] = datetime.datetime.now().isoformat()

        data.append(document)
        if self._save_collection(collection_name, data):
            return document['id']
        return None

    def find(self, collection_name, query=None):
        """Find documents in a collection matching a query"""
        data = self._load_collection(collection_name)

        if not query:
            return data

        # Simple query matching (exact matches only)
        results = []
        for doc in data:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                results.append(doc)

        return results

    def find_one(self, collection_name, query):
        """Find a single document in a collection matching a query"""
        results = self.find(collection_name, query)
        return results[0] if results else None

    def update_one(self, collection_name, query, update):
        """Update a document in a collection"""
        data = self._load_collection(collection_name)
        updated = False

        for i, doc in enumerate(data):
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break

            if match:
                # Update document
                for key, value in update.items():
                    data[i][key] = value
                data[i]['updated'] = datetime.datetime.now().isoformat()
                updated = True
                break

        if updated:
            self._save_collection(collection_name, data)
            return True
        return False

    def delete_one(self, collection_name, query):
        """Delete a document from a collection"""
        data = self._load_collection(collection_name)

        # Filter out documents matching the query
        filtered_data = []
        deleted = False

        for doc in data:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break

            if match and not deleted:
                deleted = True
            else:
                filtered_data.append(doc)

        if deleted:
            self._save_collection(collection_name, filtered_data)
            return True
        return False

# Singleton instance
_instance = None

def get_local_storage():
    global _instance
    if _instance is None:
        _instance = LocalStorage()
    return _instance
