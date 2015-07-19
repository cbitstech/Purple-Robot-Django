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
        # print('Unsized: ' + str(PurpleRobotReading.objects.filter(size=0).count()))
        
        readings = PurpleRobotReading.objects.filter(size=0)[:2000]

        for reading in readings:
            reading.size = len(reading.payload)
            reading.save()
