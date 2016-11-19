# pylint: disable=line-too-long, no-member, invalid-name

import os

from collections import namedtuple

from django.core.management.base import BaseCommand
from django.test.client import RequestFactory

from purple_robot_app.models import PurpleRobotDevice
from purple_robot_app.views import pr_device


class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/refresh_device_pages.lock', os.R_OK):
            return

        open('/tmp/refresh_device_pages.lock', 'w').close()

        FakeRequest = namedtuple('FakeRequest', ['is_active', 'is_staff'])

        factory = RequestFactory()

        request = factory.get('/pr/devices/foobar')
        request.user = FakeRequest(is_active=True, is_staff=True)

        for device in PurpleRobotDevice.objects.all():
            pr_device(request, device.device_id)

        os.remove('/tmp/refresh_device_pages.lock')
