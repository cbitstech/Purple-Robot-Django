import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotEvent, \
                                    PurpleRobotPayload

class Command(BaseCommand):
    def handle(self, *args, **options):
        print('Rename ' + args[0] + ' to ' + args[1] + '...')
        
        readings = PurpleRobotReading.objects.filter(user_id=args[0])
        
        print('Original reading count: ' + str(readings.count()))
        
        updated = readings.update(user_id=args[1])

        print('Updated reading count: ' + str(updated))
        
