import datetime
import hashlib
import json
import requests
import os
import sys
import time

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/size_readings.lock', os.R_OK):
            t = os.path.getmtime('/tmp/size_readings.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('size_readings: Stale lock - removing...')
                os.remove('/tmp/size_readings.lock')
            else:
                return

        touch('/tmp/size_readings.lock')
        
        readings = PurpleRobotReading.objects.filter(size=0).order_by('-logged')[:2000]

        for reading in readings:
            reading.size = len(reading.payload)
            reading.save()

        os.remove('/tmp/size_readings.lock')
