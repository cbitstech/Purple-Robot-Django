import datetime
import json
import os

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload, PurpleRobotEvent

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/delete_older_data.lock', os.R_OK):
            t = os.path.getmtime('/tmp/delete_older_data.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('delete_older_data: Stale lock - removing...')
                os.remove('/tmp/delete_older_data.lock')
            else:
                return

        touch('/tmp/delete_older_data.lock')
        
        end = datetime.datetime.now() - datetime.timedelta(days=14)
        
        PurpleRobotPayload.objects.filter(added__lte=end).delete()
        PurpleRobotReading.objects.filter(logged__lte=end).delete()
        PurpleRobotEvent.objects.filter(logged__lte=end).delete()
        
        os.remove('/tmp/delete_older_data.lock')
