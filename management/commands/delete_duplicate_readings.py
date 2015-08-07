import json
import os

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/delete_duplicate_readings.lock', os.R_OK):
            t = os.path.getmtime('/tmp/delete_duplicate_readings.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('delete_duplicate_readings: Stale lock - removing...')
                os.remove('/tmp/delete_duplicate_readings.lock')
            else:
                return

        touch('/tmp/delete_duplicate_readings.lock')

        guids = PurpleRobotReading.objects.order_by().values_list('guid', flat=True).distinct()
        
        for guid in guids:
            count = PurpleRobotReading.objects.filter(guid=guid).count()
           
            if count > 1:
                for match in PurpleRobotReading.objects.filter(guid=guid)[1:]:
                    match.delete()

        os.remove('/tmp/delete_duplicate_readings.lock')
