from django.core.management.base import BaseCommand
import os
import sys
import subprocess
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Start a local MongoDB server'

    def handle(self, *args, **options):
        # Path to the start_local_mongodb.py script
        script_path = os.path.join(settings.BASE_DIR, 'start_local_mongodb.py')
        
        if not os.path.exists(script_path):
            self.stdout.write(self.style.ERROR(f"Script not found: {script_path}"))
            return
        
        self.stdout.write(self.style.SUCCESS("Starting local MongoDB server..."))
        
        try:
            # Start the local MongoDB server
            process = subprocess.Popen([sys.executable, script_path], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
            
            # Wait a bit to see if there are any immediate errors
            stdout, stderr = process.communicate(timeout=5)
            
            if process.returncode is not None and process.returncode != 0:
                self.stdout.write(self.style.ERROR(f"Failed to start MongoDB: {stderr.decode()}"))
            else:
                self.stdout.write(self.style.SUCCESS("MongoDB server started successfully"))
                self.stdout.write(self.style.SUCCESS("Data is being stored locally in the mongodb_data directory"))
        except subprocess.TimeoutExpired:
            # This is actually good - it means the process is still running
            self.stdout.write(self.style.SUCCESS("MongoDB server started successfully"))
            self.stdout.write(self.style.SUCCESS("Data is being stored locally in the mongodb_data directory"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error starting MongoDB: {e}"))
