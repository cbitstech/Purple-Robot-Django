import datetime
import json
import os
import pytz

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/extracted_readings.lock', os.R_OK):
            return
    
        open('/tmp/extracted_readings.lock', 'wa').close() 

        tag = 'extracted_readings'
        
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('-added')[:250]
        
        while payloads.count() > 0:
            for payload in payloads:
                payload.ingest_readings()
                    
            payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('-added')[:250]
            
        readings = PurpleRobotReading.objects.filter(guid=None)[:250]
        
        for reading in readings:
            reading.update_guid()

        os.remove('/tmp/extracted_readings.lock')
