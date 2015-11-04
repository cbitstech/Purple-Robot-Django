import datetime
import hashlib
import json
import requests
import os
import sys
import time

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotDevice

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/size_readings.lock', os.R_OK):
            t = os.path.getmtime('/tmp/size_readings.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 4 * 60 * 60:
                print('size_readings: Stale lock - removing...')
                os.remove('/tmp/size_readings.lock')
            else:
                return

        touch('/tmp/size_readings.lock')
        
        readings = list(PurpleRobotReading.objects.filter(size=0)[:1000])
        count = PurpleRobotReading.objects.filter(size=0).count()
        
        while count > 0:
            print('READINGS: ' + str(count) + ' -- ' + str(datetime.datetime.now()))
            
            for reading in readings:
                device = None # PurpleRobotDevice.objects.filter(hash_key=reading.user_id).first()

                reading.size = len(reading.payload)
    
                if reading.attachment != None:
                    try:
                        reading.size += reading.attachment.size
                    except ValueError:
                        pass # No attachment...
    
                reading.save()
            
                if device != None:
                    metadata = json.loads(device.performance_metadata)
            
                    if ('total_readings_size' in metadata) == False:
                        total_size = PurpleRobotReading.objects.filter(user_id=device.hash_key).aggregate(Sum('size'))
                        metadata['total_readings_size'] = total_size['size__sum']
                
                    if ('total_readings_size' in metadata) == False or metadata['total_readings_size'] == None:
                        metadata['total_readings_size'] = 0

                    metadata['total_readings_size'] += reading.size
            
                    device.performance_metadata = json.dumps(metadata, indent=2)
                    device.save()
                
            touch('/tmp/size_readings.lock')

            count -= len(readings)
            readings = list(PurpleRobotReading.objects.filter(size=0)[:1000])                
            # count = PurpleRobotReading.objects.filter(size=0).count()

        os.remove('/tmp/size_readings.lock')
