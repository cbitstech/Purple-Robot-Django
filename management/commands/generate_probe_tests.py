# pylint: disable=line-too-long, no-member

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from ...models import PurpleRobotTest, PurpleRobotDevice

REPORT_DAYS = 1


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.all():
            user_id = device.user_hash()

            for reading in device.last_readings(omit_readings=True):
                probe = reading['full_probe_name']

                if PurpleRobotTest.objects.filter(user_id=user_id, probe=probe).count() == 0:
                    PurpleRobotTest(user_id=user_id, probe=probe, active=True, last_updated=timezone.now(), slug=slugify(device.device_id + '-' + reading['name'])).save()

                    print 'Added test ' + device.device_id + '/' + reading['name']
