import hashlib

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotEvent, \
                                    PurpleRobotPayload

class Command(BaseCommand):
    def handle(self, *args, **options):
        m = hashlib.md5()
        m.update(args[0])
        
        user_id = m.hexdigest()
        
        print('Hash for ' + args[0] + ': ' + user_id)
