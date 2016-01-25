# pylint: disable=line-too-long

import datetime

from django.utils import timezone

from purple_robot_app.performance import append_performance_sample


def log_reading(reading):
    yesterday = timezone.now() - datetime.timedelta(days=1)

    if reading.logged > yesterday:
        append_performance_sample(reading.user_id, reading.probe, reading.logged, {'sample_count': 1})
