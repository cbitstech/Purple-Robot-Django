import datetime
import json
import pytz
import urllib
import urllib2

from django.core.management.base import BaseCommand, CommandError

from purple_robot_app.models import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        readings = PurpleRobotReading.objects.filter(guid=None)[:1000]
        
        for reading in readings:
            payload = json.loads(reading.payload)
            reading.guid = payload['GUID']
            reading.save()
