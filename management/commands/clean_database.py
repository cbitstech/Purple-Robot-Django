import datetime
import json
import pytz
import tempfile
import urllib
import urllib2

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from purple_robot_app.models import *

DAYS_KEPT = 21

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        start = now - datetime.timedelta(DAYS_KEPT)
        
        PurpleRobotReading.objects.filter(logged__lte=start).delete()
        PurpleRobotEvent.objects.filter(logged__lte=start).delete()
        PurpleRobotPayload.objects.filter(added__lte=start).delete()
