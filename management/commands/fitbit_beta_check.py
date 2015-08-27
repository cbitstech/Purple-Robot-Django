import json

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading

class Command(BaseCommand):
    def handle(self, *args, **options):
        seen = {}
        
        keys = [ 'HEART', 'FLOORS', 'ELEVATION', 'DISTANCE', 'CALORIES', 'STEPS' ]
        
        for reading in PurpleRobotReading.objects.filter(user_id='073adb668d74a6aaa7d452eb9f804c99', probe='edu.northwestern.cbits.purple_robot_manager.probes.services.FitbitBetaProbe').order_by('logged'):
            payload = json.loads(reading.payload)
            
            for key in keys:
                values = payload[key]
                
                if key == 'STEPS':
                    key = 'STEP'
                
                times = payload[key + '_TIMESTAMPS']
                
                for i in range(0, len(values)):
                    value = values[i]
                    time = times[i]
                    
                    seen_key = key + '_' + str(time)
                    
                    if seen_key in seen:
                        print('DUPE VALUE: ' + seen_key + ' - O: ' + str(seen[seen_key]) + ' N: ' + str(value) + ' --> ' + reading.guid)
                        
                    seen[seen_key] = value
            
            
