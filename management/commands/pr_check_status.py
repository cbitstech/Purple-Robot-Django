# pylint: disable=line-too-long, no-member

import os
import datetime
import sys

from django.core.management import call_command, get_commands, find_commands
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ...models import PurpleRobotAlert, PurpleRobotDevice


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


def fetch_query(message=None, severity=None, tags=None, user_id=None, probe=None, dismissed=False):
    query = Q(dismissed=None)

    if dismissed:
        query = Q(dismissed__lte=timezone.now())

    if message is not None:
        query = query & Q(message=message)

    if severity is not None:
        query = query & Q(severity=severity)

    if tags is not None:
        query = query & Q(tags__contains=tags)

    if user_id is not None:
        query = query & Q(user_id=user_id)

    if probe is not None:
        query = query & Q(probe=probe)

    return query


def log_alert(message=None, severity=None, tags=None, user_id=None, probe=None):
    query = fetch_query(None, None, tags, user_id, probe)

    now = timezone.now()

    alerts = PurpleRobotAlert.objects.filter(query)

    if alerts.count() > 0:
        for alert in alerts:
            if message is not None:
                alert.message = message

            if severity is not None:
                alert.severity = severity

            alert.save()
    else:
        alert = PurpleRobotAlert(message=message, severity=severity, tags=tags, probe=probe, user_id=user_id, generated=now)
        alert.save()


def cancel_alert(message=None, severity=None, tags=None, user_id=None, probe=None):
    query = fetch_query(message, severity, tags, user_id, probe)

    now = timezone.now()

    for alert in PurpleRobotAlert.objects.filter(query):
        alert.dismissed = now
        alert.manually_dismissed = True

        alert.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/check_status.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/check_status.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 6 * 60 * 60:
                print 'check_status: Stale lock - removing...'
                os.remove('/tmp/check_status.lock')
            else:
                return

        touch('/tmp/check_status.lock')

        for command_name, package in get_commands().iteritems():
            if command_name.startswith('pr_status_check_'):
                touch('/tmp/check_status.lock')
                
                sys.stdout.flush()

                call_command(command_name)
                
        touch('/tmp/check_status.lock')

        for device in PurpleRobotDevice.objects.filter(mute_alerts=True):
            for alert in PurpleRobotAlert.objects.filter(user_id=device.hash_key, dismissed=None):
                alert.dismissed = timezone.now()
                alert.save()

        os.remove('/tmp/check_status.lock')
