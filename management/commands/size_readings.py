# pylint: disable=line-too-long, no-member

import datetime
import json
import os
import time

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from ...models import PurpleRobotReading, PurpleRobotDevice


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/size_readings.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/size_readings.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 4 * 60 * 60:
                print 'size_readings: Stale lock - removing...'
                os.remove('/tmp/size_readings.lock')
            else:
                return

        touch('/tmp/size_readings.lock')

        readings = list(PurpleRobotReading.objects.filter(size=0)[:1000])
        count = PurpleRobotReading.objects.filter(size=0).count()

        while count > 0:
            for reading in readings:
                reading.size = len(reading.payload)

                if reading.attachment is not None:
                    try:
                        reading.size += reading.attachment.size
                    except ValueError:
                        pass  # No attachment...

                reading.save()

            touch('/tmp/size_readings.lock')

            count -= len(readings)
            readings = list(PurpleRobotReading.objects.filter(size=0)[:1000])

        for device in PurpleRobotDevice.objects.order_by('device_id'):
            now = timezone.now()

            metadata = json.loads(device.performance_metadata)

            last_readings_size = 0

            if 'last_readings_size' in metadata:
                last_readings_size = metadata['last_readings_size']

            last_readings_size = datetime.datetime.fromtimestamp(last_readings_size, tz=now.tzinfo)

            if (now - last_readings_size).total_seconds() > 60 * 60 * 4:
                if 'total_readings_size' in metadata:
                    del metadata['total_readings_size']

            if ('total_readings_size' in metadata) == False:
                total_size = PurpleRobotReading.objects.filter(user_id=device.hash_key).aggregate(Sum('size'))
                metadata['total_readings_size'] = total_size['size__sum']

                metadata['last_readings_size'] = time.mktime(now.timetuple())

            device.performance_metadata = json.dumps(metadata, indent=2)
            device.save()

        os.remove('/tmp/size_readings.lock')
