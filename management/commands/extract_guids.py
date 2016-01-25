# pylint: disable=line-too-long, no-member

import json

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        readings = PurpleRobotReading.objects.filter(guid=None)[:5000]

        for reading in readings:
            payload = json.loads(reading.payload)
            reading.guid = payload['GUID']
            reading.save()
