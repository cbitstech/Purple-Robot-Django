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
        
        readings = PurpleRobotReading.objects.filter(size=0).order_by('-logged')[:2000]

        for reading in readings:
            reading.size = len(reading.payload)
            
            if reading.attachment != None:
                try:
                    reading.size += reading.attachment.size
                except ValueError:
                    pass # No attachment...
            
            reading.save()
            
            touch('/tmp/size_readings.lock')

            
        for device in PurpleRobotDevice.objects.all():
            total_size = PurpleRobotReading.objects.filter(user_id=device.hash_key).aggregate(Sum('size'))
            
            metadata = json.loads(device.performance_metadata)
            
            metadata['total_readings_size'] = total_size['size__sum']
            
            device.performance_metadata = json.dumps(metadata, indent=2)
            
            device.save()

            touch('/tmp/size_readings.lock')

        os.remove('/tmp/size_readings.lock')
