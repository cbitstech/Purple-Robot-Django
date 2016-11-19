# pylint: disable=line-too-long, no-member

import arrow
import datetime
import os
import pytz

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from purple_robot_app.models import PurpleRobotPayload
from purple_robot_app.performance import append_performance_sample


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/gather_statistics.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/gather_statistics.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 6 * 60 * 60:
                print 'gather_statistics: Stale lock - removing...'
                os.remove('/tmp/gather_statistics.lock')
            else:
                return

        touch('/tmp/gather_statistics.lock')

        here_tz = pytz.timezone(settings.TIME_ZONE)
        now = arrow.get(timezone.now().astimezone(here_tz))

        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0).datetime
        start_hour = now.datetime - datetime.timedelta(hours=1)

        count = PurpleRobotPayload.objects.filter(added__gte=start_hour).count()
        append_performance_sample('system', 'uploads_hour', timezone.now(), {'count': count})

        count = PurpleRobotPayload.objects.filter(added__gte=start_today).count()
        append_performance_sample('system', 'uploads_today', timezone.now(), {'count': count})

        tag = 'extracted_into_database'
        skip_tag = 'extracted_into_database_skip'

        count = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        append_performance_sample('system', 'pending_mirror_payloads', timezone.now(), {'count': count})

        count = PurpleRobotPayload.objects.filter(process_tags__contains=skip_tag).count()
        append_performance_sample('system', 'skipped_mirror_payloads', timezone.now(), {'count': count})

        week = now.datetime - datetime.timedelta(days=7)
        day = now.datetime - datetime.timedelta(days=1)
        half_day = now.datetime - datetime.timedelta(hours=12)
        quarter_day = now.datetime - datetime.timedelta(hours=6)
        hour = now.datetime - datetime.timedelta(hours=1)

        week_count = PurpleRobotPayload.objects.filter(added__lt=week).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        day_count = PurpleRobotPayload.objects.filter(added__gte=week, added__lt=day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        half_day_count = PurpleRobotPayload.objects.filter(added__gte=day, added__lt=half_day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        quarter_day_count = PurpleRobotPayload.objects.filter(added__gte=half_day, added__lt=quarter_day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        hour_count = PurpleRobotPayload.objects.filter(added__gte=quarter_day, added__lt=hour).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        less_hour_count = PurpleRobotPayload.objects.filter(added__gte=hour).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()

        append_performance_sample('system', 'pending_mirror_ages', timezone.now(), {
            'week_count': week_count,
            'day_count': day_count,
            'half_day_count': half_day_count,
            'quarter_day_count': quarter_day_count,
            'hour_count': hour_count,
            'less_hour_count': less_hour_count
        })

        tag = 'extracted_readings'
        skip_tag = 'ingest_error'

        count = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        append_performance_sample('system', 'pending_ingest_payloads', timezone.now(), {'count': count})

        count = PurpleRobotPayload.objects.filter(process_tags__contains=skip_tag).count()
        append_performance_sample('system', 'skipped_ingest_payloads', timezone.now(), {'count': count})

        week_count = PurpleRobotPayload.objects.filter(added__lt=week).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        day_count = PurpleRobotPayload.objects.filter(added__gte=week, added__lt=day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        half_day_count = PurpleRobotPayload.objects.filter(added__gte=day, added__lt=half_day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        quarter_day_count = PurpleRobotPayload.objects.filter(added__gte=half_day, added__lt=quarter_day).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        hour_count = PurpleRobotPayload.objects.filter(added__gte=quarter_day, added__lt=hour).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()
        less_hour_count = PurpleRobotPayload.objects.filter(added__gte=hour).exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).count()

        append_performance_sample('system', 'pending_ingest_ages', timezone.now(), {
            'week_count': week_count,
            'day_count': day_count,
            'half_day_count': half_day_count,
            'quarter_day_count': quarter_day_count,
            'hour_count': hour_count,
            'less_hour_count': less_hour_count
        })

        uptime = os.popen("/usr/bin/uptime").read()
        uptime = uptime.split('load average: ')[1].split(" ")

        load_minute = float(uptime[0].replace(',', '').strip())
        load_five = float(uptime[1].replace(',', '').strip())
        load_fifteen = float(uptime[2].replace(',', '').strip())

        append_performance_sample('system', 'server_performance', timezone.now(), {'load_minute': load_minute, 'load_five': load_five, 'load_fifteen': load_fifteen})

        counts = []

        index_time = start_today

        while (index_time + datetime.timedelta(seconds=(15 * 60))) < timezone.now():
            end = index_time + datetime.timedelta(seconds=(30 * 60))

            plot = index_time + datetime.timedelta(seconds=(15 * 60))

            counts.append({'date': plot.isoformat(), 'count': PurpleRobotPayload.objects.filter(added__gte=index_time, added__lt=end).count()})

            index_time = end

        append_performance_sample('system', 'payload_uploads', timezone.now(), {'counts': counts})

        os.remove('/tmp/gather_statistics.lock')
