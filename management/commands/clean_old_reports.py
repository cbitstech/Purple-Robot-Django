# pylint: disable=line-too-long, no-member

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import PurpleRobotReport

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.SignificantMotionProbe'


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        start = now - datetime.timedelta(1)

        PurpleRobotReport.objects.filter(generated__lte=start).delete()
