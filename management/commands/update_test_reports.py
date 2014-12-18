from django.core.management.base import BaseCommand, CommandError

from purple_robot_app.models import *

REPORT_DAYS = 2

class Command(BaseCommand):
    def handle(self, *args, **options):
        for test in PurpleRobotTest.objects.all():
            test.update(days=REPORT_DAYS)
