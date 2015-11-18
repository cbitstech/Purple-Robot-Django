from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotTest

REPORT_DAYS = 1

class Command(BaseCommand):
    def handle(self, *args, **options):
        pass
        # test = PurpleRobotTest.objects.all().order_by('last_updated').first()
        # test.update(days=REPORT_DAYS)
