from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotPayload
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            payload = PurpleRobotPayload.objects.filter(user_id=device.hash_key).order_by('-added').first()
            
            now = timezone.now()
            
            if payload == None:
                log_alert(message='No payloads have been uploaded yet.', severity=1, tags='device_last_upload', user_id=device.hash_key)
            elif (now - payload.added).total_seconds() > (60 * 60 * 12):
                log_alert(message='No payloads have been uploaded in the last 12 hours.', severity=2, tags='device_last_upload', user_id=device.hash_key)
            else:
                cancel_alert(tags='device_last_upload', user_id=device.hash_key)
