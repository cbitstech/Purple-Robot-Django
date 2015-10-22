import datetime
import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotReading, my_slugify
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

HARDWARE_PROBE = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.HardwareInformationProbe'

TAG = 'device_hardware_changed'

class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            start = timezone.now() - datetime.timedelta(days=3)
            
            mac = None
            same_mac = True
            
            for reading in PurpleRobotReading.objects.filter(user_id=device.hash_key, probe=HARDWARE_PROBE, logged__gte=start):
                payload = json.loads(reading.payload)
                
                if 'WIFI_MAC' in payload:
                    if mac == None:
                        mac = payload['WIFI_MAC']
                    elif mac != payload['WIFI_MAC']:
                        same_mac = False
            
            if same_mac:
                cancel_alert(tags=TAG, user_id=device.hash_key)
            else:
                log_alert(message='Device hardware changed.', severity=2, tags=TAG, user_id=device.hash_key)
