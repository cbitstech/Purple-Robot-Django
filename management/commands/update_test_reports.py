# pylint: disable=line-too-long

from django.core.management.base import BaseCommand

from ...models import PurpleRobotTest

REPORT_DAYS = 1


class Command(BaseCommand):
    def handle(self, *args, **options):
        test = PurpleRobotTest.objects.all().order_by('last_updated').first()
        test.update(days=REPORT_DAYS)
