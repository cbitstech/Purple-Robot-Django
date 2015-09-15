import datetime
import json
import os
import pytz

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/extract_readings.lock', os.R_OK):
            t = os.path.getmtime('/tmp/extract_readings.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('extract_readings: Stale lock - removing...')
                os.remove('/tmp/extract_readings.lock')
            else:
                return

        touch('/tmp/extract_readings.lock')

        tag = 'extracted_readings'
        
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('-added')[:250]
        
        while payloads.count() > 0:
            for payload in payloads:
                payload.ingest_readings()
                    
            payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains='ingest_error').order_by('-added')[:250]
            
        readings = PurpleRobotReading.objects.filter(guid=None)[:250]
        
        for reading in readings:
            reading.update_guid()

        os.remove('/tmp/extract_readings.lock')
