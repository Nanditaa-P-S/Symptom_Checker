from django.core.management.base import BaseCommand
import os
import sys
import subprocess
from django.conf import settings

class Command(BaseCommand):
    help = 'Stop the local MongoDB server'

    def handle(self, *args, **options):
        # Path to the start_local_mongodb.py script
        script_path = os.path.join(settings.BASE_DIR, 'start_local_mongodb.py')
        
        if not os.path.exists(script_path):
            self.stdout.write(self.style.ERROR(f"Script not found: {script_path}"))
            return
        
        self.stdout.write(self.style.SUCCESS("Stopping local MongoDB server..."))
        
        try:
            # Stop the local MongoDB server
            process = subprocess.Popen([sys.executable, script_path, 'stop'], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.stdout.write(self.style.ERROR(f"Failed to stop MongoDB: {stderr.decode()}"))
            else:
                self.stdout.write(self.style.SUCCESS("MongoDB server stopped successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error stopping MongoDB: {e}"))
