# pylint: disable=line-too-long, no-member

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotDevice
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            level = device.last_battery()

            if level >= 33:
                cancel_alert(tags='device_last_battery', user_id=device.hash_key)
            elif level >= 25:
                log_alert(message='Battery level is less than 33%.', severity=1, tags='device_last_battery', user_id=device.hash_key)
            else:
                log_alert(message='Battery level is less than 25%.', severity=2, tags='device_last_battery', user_id=device.hash_key)
