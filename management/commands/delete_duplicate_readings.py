# pylint: disable=line-too-long, no-member

import datetime
import os

from django.core.management.base import BaseCommand

from ...models import PurpleRobotReading, PurpleRobotDevice


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if True:
            return  # Disable this command!

        if os.access('/tmp/delete_duplicate_readings.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/delete_duplicate_readings.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 120:
                print 'delete_duplicate_readings: Stale lock - removing...'
                os.remove('/tmp/delete_duplicate_readings.lock')
            else:
                return

        touch('/tmp/delete_duplicate_readings.lock')

        for device in PurpleRobotDevice.objects.all().order_by('device_id'):
            guids = PurpleRobotReading.objects.filter(user_id=device.hash_key).order_by('guid').values_list('guid', flat=True).distinct()

            for guid in guids:
                if guid is not None:
                    count = PurpleRobotReading.objects.filter(guid=guid, user_id=device.hash_key).count()

                    if count > 1:
                        for match in PurpleRobotReading.objects.filter(guid=guid)[1:]:
                            match.delete()

        os.remove('/tmp/delete_duplicate_readings.lock')
