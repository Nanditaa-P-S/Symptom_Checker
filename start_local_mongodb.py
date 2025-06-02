"""
Script to start a local MongoDB server that stores data in a local directory.
This allows MongoDB to be used as a local database without requiring a system-wide installation.
"""

import os
import sys
import subprocess
import time
import signal
import atexit
import platform
import tempfile
from pathlib import Path

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Directory to store MongoDB data files
DATA_DIR = os.path.join(BASE_DIR, 'mongodb_data')
LOG_DIR = os.path.join(BASE_DIR, 'mongodb_logs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# MongoDB binary paths - you'll need to adjust these based on your MongoDB installation
if platform.system() == 'Windows':
    MONGODB_BIN = r'C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe'
    if not os.path.exists(MONGODB_BIN):
        # Try to find MongoDB in common installation locations
        possible_paths = [
            r'C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe',
            r'C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe',
            r'C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                MONGODB_BIN = path
                break
else:
    MONGODB_BIN = 'mongod'  # Assume it's in the PATH on Linux/Mac

# MongoDB configuration
MONGODB_PORT = 27017
PID_FILE = os.path.join(tempfile.gettempdir(), 'local_mongodb.pid')

def is_mongodb_running():
    """Check if MongoDB is already running on the specified port."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', MONGODB_PORT))
    sock.close()
    return result == 0

def start_mongodb():
    """Start a local MongoDB server."""
    if is_mongodb_running():
        print(f"MongoDB is already running on port {MONGODB_PORT}")
        return True

    # Command to start MongoDB with local storage
    # Using a more direct configuration approach
    cmd = [
        MONGODB_BIN,
        '--dbpath', DATA_DIR,
        '--port', str(MONGODB_PORT),
        '--logpath', os.path.join(LOG_DIR, 'mongodb.log'),
        '--logappend',
        '--bind_ip', 'localhost',
        '--noscripting',  # Disable JavaScript execution
        '--nojournal',    # Disable journaling for better performance in development
    ]

    try:
        # Start MongoDB as a subprocess
        print(f"Starting MongoDB with data directory: {DATA_DIR}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Save the process ID to a file
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))

        # Wait a bit to make sure MongoDB starts
        time.sleep(2)

        # Check if MongoDB started successfully
        if is_mongodb_running():
            print(f"MongoDB started successfully on port {MONGODB_PORT}")
            return True
        else:
            print("Failed to start MongoDB")
            return False
    except Exception as e:
        print(f"Error starting MongoDB: {e}")
        return False

def stop_mongodb():
    """Stop the local MongoDB server."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())

            # Try to terminate the process
            if platform.system() == 'Windows':
                subprocess.call(['taskkill', '/F', '/PID', str(pid)])
            else:
                os.kill(pid, signal.SIGTERM)

            # Remove the PID file
            os.remove(PID_FILE)
            print("MongoDB stopped")
        except Exception as e:
            print(f"Error stopping MongoDB: {e}")
    else:
        print("MongoDB is not running or PID file not found")

# Register the stop function to be called when the script exits
atexit.register(stop_mongodb)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stop':
        stop_mongodb()
    else:
        start_mongodb()
