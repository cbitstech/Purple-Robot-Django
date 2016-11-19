# pylint: disable=line-too-long, no-member

import datetime
import gzip
import json
import tempfile

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot.settings import REPORT_DEVICES
from purple_robot_app.models import PurpleRobotReading, PurpleRobotReport

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.SignificantMotionProbe'


class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = REPORT_DEVICES  # PurpleRobotPayload.objects.order_by().values('user_id').distinct()

        start = datetime.datetime.now() - datetime.timedelta(days=21)

        for user_hash in hashes:
            payloads = PurpleRobotReading.objects.filter(user_id=user_hash, probe=PROBE_NAME, logged__gte=start).order_by('logged')

            count = payloads.count()
            if count > 0:
                temp_file = tempfile.TemporaryFile()
                gzf = gzip.GzipFile(mode='wb', fileobj=temp_file)

                gzf.write('User ID\tTimestamp\n')

                index = 0

                while index < count:
                    end = index + 100

                    if end > count:
                        end = count

                    for payload in payloads[index:end]:
                        reading_json = json.loads(payload.payload)

                        gzf.write(hash + '\t' + str(reading_json['TIMESTAMP']) + '\n')

                    index += 100

                gzf.flush()
                gzf.close()

                temp_file.seek(0)

                report = PurpleRobotReport(generated=timezone.now(), mime_type='application/x-gzip', probe=PROBE_NAME, user_id=user_hash)
                report.save()
                report.report_file.save(hash + '-significant-motion.txt.gz', File(temp_file))
                report.save()
