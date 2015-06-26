from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotPayload, PurpleRobotReading
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.all():
            payload = PurpleRobotPayload.objects.filter(user_id=device.hash_key).order_by('-added').first()
            reading = PurpleRobotReading.objects.filter(user_id=device.hash_key).order_by('-logged').first()
            
            if payload != None and reading != None:
                diff = payload.added - reading.logged
                
                seconds = diff.total_seconds()
            
                if seconds < (10 * 60):            
                    cancel_alert(tags='device_payload_reading_gap', user_id=device.hash_key)
                elif seconds < (30 * 60):            
                    log_alert(message='{0:.2f}'.format(seconds / 60) + ' minute gap between payload and reading.', severity=1, tags='device_payload_reading_gap', user_id=device.hash_key)
                else:
                    log_alert(message='{0:.2f}'.format(seconds / 60) + ' minute gap between payload and reading.', severity=2, tags='device_payload_reading_gap', user_id=device.hash_key)
