import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotEvent, \
                                    PurpleRobotPayload

DAYS_KEPT = 21

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        start = now - datetime.timedelta(DAYS_KEPT)
        
        PurpleRobotReading.objects.filter(logged__lte=start).delete()
        PurpleRobotEvent.objects.filter(logged__lte=start).delete()
        PurpleRobotPayload.objects.filter(added__lte=start).delete()
