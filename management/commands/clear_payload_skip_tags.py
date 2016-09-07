# pylint: disable=line-too-long, no-member

import datetime
import os

from django.core.management.base import BaseCommand

from ...models import PurpleRobotPayload

PRINT_PROGRESS = False

SKIP_TAG = 'extracted_into_database_skip'


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/clear_payload_skip_tags.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/clear_payload_skip_tags.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 300:
                print 'clear_payload_skip_tags: Stale lock - removing...'
                os.remove('/tmp/clear_payload_skip_tags.lock')
            else:
                return

        touch('/tmp/clear_payload_skip_tags.lock')

        payloads = list(PurpleRobotPayload.objects.filter(process_tags__contains=SKIP_TAG).order_by('-added')[:250])

        count = 0

        while len(payloads) > 0 and count < 20:
            count += 1

            for payload in payloads:
                payload.process_tags = payload.process_tags.replace(SKIP_TAG, '')

                while payload.process_tags.find('  ') != -1:
                    payload.process_tags = payload.process_tags.replace('  ', ' ')

                payload.process_tags = payload.process_tags.strip()

                touch('/tmp/clear_payload_skip_tags.lock')

                payload.save()

            payloads = list(PurpleRobotPayload.objects.filter(process_tags__contains=SKIP_TAG).order_by('-added')[:250])

        os.remove('/tmp/clear_payload_skip_tags.lock')
