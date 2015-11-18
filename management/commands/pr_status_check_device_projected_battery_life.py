from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            cancel_alert(tags='device_projected_lifetime', user_id=device.hash_key)

#            lifetime = device.projected_battery_lifetime() / (60 * 60)
#            
#            if lifetime == -1:            
#                log_alert(message='Unable to project device lifetime.', severity=1, tags='device_projected_lifetime', user_id=device.hash_key)
#            elif lifetime > 8:            
#                cancel_alert(tags='device_projected_lifetime', user_id=device.hash_key)
#            elif lifetime > 6:
#                log_alert(message='Device lifetime is estimated to be {0:.2f} hours.'.format(lifetime), severity=1, tags='device_projected_lifetime', user_id=device.hash_key)
#            else:
#                log_alert(message='Device lifetime is estimated to be {0:.2f} hours.'.format(lifetime), severity=2, tags='device_projected_lifetime', user_id=device.hash_key)
