import json
import os

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/delete_duplicate_readings.lock', os.R_OK):
            return
    
        open('/tmp/delete_duplicate_readings.lock', 'wa').close() 

        guids = PurpleRobotReading.objects.order_by().values_list('guid', flat=True).distinct()
        
        for guid in guids:
            count = PurpleRobotReading.objects.filter(guid=guid).count()
           
            if count > 1:
                for match in PurpleRobotReading.objects.filter(guid=guid)[1:]:
                    match.delete()

        os.remove('/tmp/delete_duplicate_readings.lock')
