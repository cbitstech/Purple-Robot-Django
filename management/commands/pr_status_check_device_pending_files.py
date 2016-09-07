# pylint: disable=line-too-long, no-member

from django.core.management.base import BaseCommand

from ...models import PurpleRobotDevice
from ...management.commands.pr_check_status import log_alert, cancel_alert


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            pending = device.last_pending_count()

            if pending < 250:
                cancel_alert(tags='device_pending_files', user_id=device.hash_key)
            elif pending < 1000:
                log_alert(message=str(pending) + ' files are awaiting upload.', severity=1, tags='device_pending_files', user_id=device.hash_key)
            else:
                log_alert(message=str(pending) + ' files are awaiting upload.', severity=2, tags='device_pending_files', user_id=device.hash_key)
