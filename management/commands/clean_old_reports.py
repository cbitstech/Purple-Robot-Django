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

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.SignificantMotionProbe'

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        start = now - datetime.timedelta(5)
        
        PurpleRobotReport.objects.filter(generated__lte=start).delete()
