import datetime
import json
import os

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading, PurpleRobotDevice

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
        
        print('1')
        for device in PurpleRobotDevice.objects.all().order_by('device_id'):
            print('2 ' + device.device_id)
            guids = PurpleRobotReading.objects.filter(user_id=device.hash_key).order_by('guid').values_list('guid', flat=True).distinct()

            print('3 ' + device.device_id + ' -- ' + str(len(guids)))
        
            for guid in guids:
                if guid != None:
                    count = PurpleRobotReading.objects.filter(guid=guid, user_id=device.hash_key).count()
               
                    if count > 1:
                        print('4 ' + guid + ' -- ' + str(count))

                        for match in PurpleRobotReading.objects.filter(guid=guid)[1:]:
                            match.delete()

        os.remove('/tmp/delete_duplicate_readings.lock')
