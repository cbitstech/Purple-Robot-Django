import hashlib
import json
import requests
import os
import sys
import time

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/size_readings.lock', os.R_OK):
            return

        open('/tmp/size_readings.lock', 'wa').close() 

        readings = PurpleRobotReading.objects.filter(size=0)[:2000]

        for reading in readings:
            reading.size = len(reading.payload)
            reading.save()

        os.remove('/tmp/size_readings.lock')
