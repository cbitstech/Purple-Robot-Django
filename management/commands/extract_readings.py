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
        
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag)[:250]
        
        while payloads.count() > 0:
            for payload in payloads:
                items = json.loads(payload.payload)

                for item in items:
                    reading = PurpleRobotReading(probe=item['PROBE'], user_id=payload.user_id)
                    reading.payload = json.dumps(item, indent=2)
                    reading.logged = datetime.datetime.utcfromtimestamp(item['TIMESTAMP']).replace(tzinfo=pytz.utc)
                    
                    reading.save()
                
                tags = payload.process_tags
                
                if tags is None or tags.find(tag) == -1:
                    if tags is None or len(tags) == 0:
                        tags = tag
                    else:
                        tags += ' ' + tag
                        
                    payload.process_tags = tags
                    
                    payload.save()
                    
            payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag)[:250]

        os.remove('/tmp/extracted_readings.lock')
